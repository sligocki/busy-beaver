#! /usr/bin/env python3
"""
Search for Lin Recurrence (as discussed in https://nickdrozd.github.io/2021/02/24/lin-recurrence-and-lins-algorithm.html)
"""

import argparse
import time
from typing import Tuple

import Direct_Simulator
import Halting_Lib
import IO

import io_pb2


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

def lin_detect_not_min(ttable,
                       max_steps : int,
                       result : io_pb2.LinRecurFilterResult) -> None:
  """Detect Lin Recurrence without knowing the period or start time.
  The result is a point at which it is in Lin Recurrence, not necessarily the
  time that it has started LR."""
  sim = Direct_Simulator.DirectSimulator(ttable)
  states_last_seen = {sim.state: sim.step_num}
  sim.step()

  while (not max_steps or sim.step_num < max_steps) and not result.success:
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
        # NOTE: We do not currently evaluate `halt_score`
        Halting_Lib.set_halting(result.status, sim.step_num, halt_score = None)
        return

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
    Halting_Lib.set_inf_recur(result.status,
                              states_to_ignore = states_used,
                              states_last_seen = states_last_seen)
    Halting_Lib.set_not_halting(result.status, "Lin_Recur")
    return
  else:
    assert sim.step_num == steps_reset, (sim.step_num, steps_reset)
    result.success = False
    # We have no information on halt_status or quasihalt_status.
    return


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


def filter(ttable,
           params : io_pb2.LinRecurFilterParams,
           result : io_pb2.LinRecurFilterResult) -> None:
  """Applies Lin Recur filter to `ttable` using `params`.
  The results are stored in `result`."""
  start_time = time.time()
  lin_detect_not_min(ttable, max_steps=params.max_steps, result=result)
  if result.success and params.find_min_start_step:
    # NOTE: result.start_step is not necessarily the earliest time that recurrence
    # starts, it is simply a time after which recurrence is in effect.

    # Do a second search, now that we know the recurrence period to find the
    # earliest start time of the recurrence.
    result.start_step = period_search(ttable, result.start_step, result.period)
  result.elapsed_time_sec = time.time() - start_time


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("tm_line", type=int, nargs="?", default=1)
  parser.add_argument("--max-steps", type=int, default = 0)
  parser.add_argument("--no-min-start-step", action="store_false",
                      dest="min_start_step")
  args = parser.parse_args()

  ttable = IO.load_TTable_filename(args.tm_file, args.tm_line)
  lr_info = io_pb2.LinRecurFilterInfo()
  lr_info.parameters.max_steps = args.max_steps
  lr_info.parameters.find_min_start_step = args.min_start_step
  filter(ttable, lr_info.parameters, lr_info.result)

  print(lr_info)

if __name__ == "__main__":
  main()
