#! /usr/bin/env python3
"""
Search for Lin Recurrence (as discussed in https://nickdrozd.github.io/2021/02/24/lin-recurrence-and-lins-algorithm.html)
"""

import argparse
import time

import Direct_Simulator
import IO
import io_pb2


def calc_quasihalt(all_states, states_used, states_last_seen):
  q_state = None
  q_last_seen = -1
  for state in all_states:
    if state not in states_used:
      if states_last_seen.get(state, -1) > q_last_seen:
        q_state = state
        q_last_seen = states_last_seen[state]

  quasihalt_info = io_pb2.QuasihaltInfo()
  if q_state == None:
    quasihalt_info.quasihalts = False
  else:
    quasihalt_info.quasihalts = True
    quasihalt_info.quasihalt_steps = q_last_seen + 1
    quasihalt_info.quasihalt_state = q_state
  return quasihalt_info


def are_half_tapes_equal(tape1, start_pos1, tape2, start_pos2, dir_offset):
  pos1 = start_pos1
  pos2 = start_pos2
  while tape1.in_range(pos1) or tape2.in_range(pos2):
    if tape1.read(pos1) != tape2.read(pos2):
      return False
    pos1 += dir_offset
    pos2 += dir_offset
  # Entire half-tapes are equal!
  return True

def are_sections_equal(start_tape, end_tape, most_left_pos, most_right_pos, offset):
  for start_pos in range(most_left_pos, most_right_pos + 1):
    end_pos = start_pos + offset
    if start_tape.read(start_pos) != end_tape.read(end_pos):
      return False
  return True

def lin_detect_not_min(ttable, max_steps=None):
  """Detect Lin Recurrence without knowing the period or start time.
  The result is a point at which it is in Lin Recurrence, not necessarily the
  time that it has started LR."""
  result = io_pb2.LinRecurInfo()
  if max_steps is not None:
    result.max_steps = max_steps
  # Not min, until period_search() is called.
  result.is_start_step_min = False

  sim = Direct_Simulator.DirectSimulator(ttable)
  states_last_seen = {sim.state: sim.step_num}
  sim.step()

  while (max_steps is None or sim.step_num < max_steps) and not result.success:
    # Instead of comparing each config to all previous configs, we try at one
    # starting steps up til 2x those steps. Then fix at 2x and repeat.
    # Thus instead of doing N^2 tape comparisons, we do N.
    # This works because once the TM repeats, it will keep repeating forever!
    init_step_num = sim.step_num
    steps_reset = 2 * init_step_num
    init_pos = sim.tape.position
    most_left_pos = most_right_pos = init_pos
    init_state = sim.state
    init_tape = sim.tape.copy()
    states_used = set()
    while sim.step_num < steps_reset and not result.success:
      states_last_seen[sim.state] = sim.step_num
      states_used.add(sim.state)
      sim.step()
      if sim.halted:
        # If a machine halts, it will never Lin Recur.
        result.success = False
        return result, io_pb2.QuasihaltInfo()

      most_left_pos = min(most_left_pos, sim.tape.position)
      most_right_pos = max(most_right_pos, sim.tape.position)
      if sim.state == init_state:
        offset = sim.tape.position - init_pos
        if offset > 0:  # Right
          if are_half_tapes_equal(init_tape, most_left_pos,
                                  sim.tape, most_left_pos + offset, dir_offset=+1):
            result.success = True
        elif offset < 0:  # Left
          if are_half_tapes_equal(init_tape, most_right_pos,
                                  sim.tape, most_right_pos + offset, dir_offset=-1):
            result.success = True
        else:  # In place
          if are_sections_equal(init_tape, sim.tape,
                                most_left_pos, most_right_pos, offset):
            result.success = True

  if result.success:
    result.start_step = init_step_num
    result.period = sim.step_num - init_step_num
    result.offset = offset
    return result, calc_quasihalt(all_states = list(range(len(ttable))),
                                  states_used = states_used,
                                  states_last_seen = states_last_seen)
  else:
    assert sim.step_num == steps_reset, (sim.step_num, steps_reset)
    result.success = False
    return result, io_pb2.QuasihaltInfo()


def check_recur(ttable, init_step, period):
  sim = Direct_Simulator.DirectSimulator(ttable)
  sim.seek(init_step)

  # Save initial tape info.
  init_pos = sim.tape.position
  most_left_pos = most_right_pos = init_pos
  init_state = sim.state
  init_tape = sim.tape.copy()

  # Run `period` steps (keeping track of range visited).
  for _ in range(period):
    sim.step()
    most_left_pos = min(most_left_pos, sim.tape.position)
    most_right_pos = max(most_right_pos, sim.tape.position)

  if sim.state == init_state:
    offset = sim.tape.position - init_pos
    if offset > 0:  # Right
      if are_half_tapes_equal(init_tape, most_left_pos,
                              sim.tape, most_left_pos + offset, dir_offset=+1):
        return True
    elif offset < 0:  # Left
      if are_half_tapes_equal(init_tape, most_right_pos,
                              sim.tape, most_right_pos + offset, dir_offset=-1):
        return True
    else:  # In place
      if are_sections_equal(init_tape, sim.tape,
                            most_left_pos, most_right_pos, offset):
        return True

  # Either states were not equal or "half-tape" was not equal, so recurrence
  # has not started yet.
  return False

# TODO: There must be a more efficient way to do this!
# For Machines/4x2-LR-158491-17620:
#  * lin_detect_not_min() takes 0.5s
#  * period_search() takes 4.5s!
def period_search(ttable, init_step, period):
  # Binary search on init_step for earliest time that recurrence began.
  low = -1          # Largest unsuccessful start of recurrence
  high = init_step  # Smallest successful start of recurrence
  while high - low > 1:
    mid = (high + low) // 2
    # print "period_search", low, mid, high
    if check_recur(ttable, mid, period):
      high = mid
    else:
      low = mid
  return high


def lin_detect(ttable, max_steps, find_min_start_step):
  start_time = time.time()
  lr_result, quasihalt_info = lin_detect_not_min(ttable, max_steps=max_steps)
  if lr_result.success and find_min_start_step:
    # NOTE: lr_result.start_step is not necessarily the earliest time that recurrence
    # starts, it is simply a time after which recurrence is in effect.

    # Do a second search, now that we know the recurrence period to find the
    # earliest start time of the recurrence.
    lr_result.start_step = period_search(ttable, lr_result.start_step, lr_result.period)
    lr_result.is_start_step_min = True
  lr_result.elapsed_time_sec = time.time() - start_time
  return lr_result, quasihalt_info


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("tm_line", type=int, nargs="?", default=1)
  parser.add_argument("--max-steps", type=int)
  parser.add_argument("--no-min-start-step", action="store_false",
                      dest="min_start_step")
  args = parser.parse_args()

  ttable = IO.load_TTable_filename(args.tm_file, args.tm_line)
  lr_result, quasihalt_info = lin_detect(ttable, args.max_steps, args.min_start_step)

  print(lr_result)
  print(quasihalt_info)

if __name__ == "__main__":
  main()
