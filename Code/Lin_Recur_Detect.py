#! /usr/bin/env python2
"""
Search for Lin Recurrence (as discussed in https://nickdrozd.github.io/2021/02/24/lin-recurrence-and-lins-algorithm.html)
"""

import argparse

import Direct_Simulator
import IO


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

def lin_search(ttable, initial_steps):
  """Detect Lin Recurrence without knowing the period or start time."""
  sim = Direct_Simulator.DirectSimulator(ttable)
  sim.seek(initial_steps)

  while True:
    # Instead of comparing each config to all previous configs, we try at one
    # starting steps up til 2x those steps. Then fix at 2x and repeat.
    # Thus instead of doing N^2 tape comparisons, we do N.
    # This works because once the TM repeats, it will keep repeating forever!
    init_step_num = sim.step_num
    steps_reset = init_step_num * 2
    init_pos = sim.tape.position
    most_left_pos = most_right_pos = init_pos
    init_state = sim.state
    init_tape = sim.tape.copy()
    while sim.step_num < steps_reset:
      sim.step()
      most_left_pos = min(most_left_pos, sim.tape.position)
      most_right_pos = max(most_right_pos, sim.tape.position)
      if sim.state == init_state:
        offset = sim.tape.position - init_pos
        if offset > 0:  # Right
          if are_half_tapes_equal(init_tape, most_left_pos,
                                  sim.tape, most_left_pos + offset, dir_offset=+1):
            print "lin_search", init_step_num, sim.step_num, sim.state, offset, most_left_pos - init_pos
            return init_step_num, (sim.step_num - init_step_num)
        elif offset < 0:  # Left
          if are_half_tapes_equal(init_tape, most_right_pos,
                                  sim.tape, most_right_pos + offset, dir_offset=-1):
            print "lin_search", init_step_num, sim.step_num, sim.state, offset, most_right_pos - init_pos
            return init_step_num, (sim.step_num - init_step_num)
        else:  # In place
          # TODO: Implement in-place checking which requires comparing entire tapes
          # (or at least the segments between most_left_pos and most_right_pos)
          pass

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
      raise Exception, "Not implemented"

  # Either states were not equal or "half-tape" was not equal, so recurrence
  # has not started yet.
  return False

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

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("tm_line", type=int, nargs="?", default=1)
  args = parser.parse_args()

  ttable = IO.load_TTable_filename(args.tm_file, args.tm_line)
  # NOTE: init_step is not necessarily the earliest time that recurrence
  # starts, it is simply a time after which recurrence is in effect.
  init_step, period = lin_search(ttable, 1)

  # Do a second search, now that we know the recurrence period to find the
  # earliest start time of the recurrence.
  recur_start = period_search(ttable, init_step, period)

  print "Found Lin Recurrence: Start:", recur_start, "Period:", period

if __name__ == "__main__":
  main()
