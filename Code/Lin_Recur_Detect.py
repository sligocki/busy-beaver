#! /usr/bin/env python3
"""
Search for Lin Recurrence (as discussed in https://nickdrozd.github.io/2021/02/24/lin-recurrence-and-lins-algorithm.html)
"""

import argparse

import Direct_Simulator
import Halting_Lib
import IO
from Macro import Turing_Machine

import io_pb2


def in_range(tape, pos):
  return tape.pos_leftmost() <= pos <= tape.pos_rightmost()

def are_half_tapes_equal(tape1, start_pos1, tape2, start_pos2, dir_offset):
  pos1 = start_pos1
  pos2 = start_pos2
  while in_range(tape1, pos1) or in_range(tape2, pos2):
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

def lin_detect_not_min(tm : Turing_Machine.Simple_Machine,
                       max_steps : int,
                       result : io_pb2.LinRecurFilterResult,
                       bb_status : io_pb2.BBStatus) -> None:
  """Detect Lin Recurrence without knowing the period or start time.
  The result is a point at which it is in Lin Recurrence, not necessarily the
  time that it has started LR."""
  sim = Direct_Simulator.DirectSimulator(tm)
  states_last_seen = {sim.state: sim.step_num}
  sim.step()

  while (not max_steps or sim.step_num < max_steps) and not result.success:
    # Brent's algorithm for loop detection:
    #   Instead of comparing each config to all previous configs, we try at one
    #   starting steps up til 2x those steps. Then fix at 2x and repeat.
    #   Thus instead of doing N^2 tape comparisons, we do N.
    #   This works because once the TM repeats, it will keep repeating forever!
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
        Halting_Lib.set_halting(bb_status,
                                halt_steps = sim.step_num,
                                halt_score = sim.halt_score,
                                from_state = sim.halt_from_state,
                                from_symbol = sim.halt_from_symbol)
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
    Halting_Lib.set_inf_recur(bb_status,
                              states_to_ignore = states_used,
                              states_last_seen = states_last_seen)
    Halting_Lib.set_not_halting(bb_status, io_pb2.INF_LIN_RECUR)
    return
  else:
    assert sim.step_num == steps_reset, (sim.step_num, steps_reset)
    result.success = False
    # We have no information on halt_status or quasihalt_status.
    return


def check_recur(tm : Turing_Machine.Simple_Machine, init_step, period):
  sim = Direct_Simulator.DirectSimulator(tm)
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
def period_search(tm : Turing_Machine.Simple_Machine, init_step, period):
  # Binary search on init_step for earliest time that recurrence began.
  low = -1          # Largest unsuccessful start of recurrence
  high = init_step  # Smallest successful start of recurrence
  while high - low > 1:
    mid = (high + low) // 2
    # print "period_search", low, mid, high
    if check_recur(tm, mid, period):
      high = mid
    else:
      low = mid
  return high


def filter(tm : Turing_Machine.Simple_Machine,
           lr_info : io_pb2.LinRecurFilterInfo,
           bb_status : io_pb2.BBStatus) -> None:
  """Applies Lin Recur filter to `tm` using `params`.
  The results are stored in `result`."""
  with IO.Timer(lr_info.result):
    lin_detect_not_min(tm, max_steps=lr_info.parameters.max_steps,
                       result=lr_info.result, bb_status=bb_status)
    if lr_info.result.success and lr_info.parameters.find_min_start_step:
      # NOTE: lr_info.result.start_step is not necessarily the earliest time that
      # recurrence starts, it is simply a time after which recurrence is in effect.

      # Do a second search, now that we know the recurrence period to find the
      # earliest start time of the recurrence.
      lr_info.result.start_step = period_search(tm, lr_info.result.start_step,
                                                lr_info.result.period)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm", help="Turing Machine or file or file:record_num (0-indexed).")
  parser.add_argument("--max-steps", type=int, default = 0)
  parser.add_argument("--no-min-start-step", action="store_false",
                      dest="min_start_step")
  args = parser.parse_args()

  lr_info = io_pb2.LinRecurFilterInfo()
  lr_info.parameters.max_steps = args.max_steps
  lr_info.parameters.find_min_start_step = args.min_start_step
  bb_status = io_pb2.BBStatus()

  tm = IO.get_tm(args.tm)
  filter(tm, lr_info, bb_status)

  print(lr_info)
  print(bb_status)

if __name__ == "__main__":
  main()
