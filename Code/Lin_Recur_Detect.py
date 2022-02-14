#! /usr/bin/env python3
"""
Search for Lin Recurrence (as discussed in https://nickdrozd.github.io/2021/02/24/lin-recurrence-and-lins-algorithm.html)
"""

import argparse

import Direct_Simulator
import IO


class Lin_Recur_Result(object):
  def __init__(self, success,
               init_step=None, period=None, offset=None,
               states_used=None, states_last_seen=None):
    self.success = success

    self.init_step = init_step
    self.period = period
    self.offset = offset

    self.states_used = states_used
    self.states_last_seen = states_last_seen

  def calc_quasihalt(self, all_states):
    q_state = None
    q_last_seen = -1
    for state in all_states:
      if state not in self.states_used:
        if self.states_last_seen.get(state, -1) > q_last_seen:
          q_state = state
          q_last_seen = self.states_last_seen[state]
    if q_state == None:
      return ("No_Quasihalt", "N/A")
    else:
      return (q_state, q_last_seen + 1)
      

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

def lin_search(ttable, max_steps=None):
  """Detect Lin Recurrence without knowing the period or start time."""
  sim = Direct_Simulator.DirectSimulator(ttable)
  states_last_seen = {sim.state: sim.step_num}
  sim.step()

  while max_steps is None or sim.step_num < max_steps:
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
    while sim.step_num < steps_reset:
      states_last_seen[sim.state] = sim.step_num
      states_used.add(sim.state)
      sim.step()
      if sim.halted:
        return Lin_Recur_Result(False)  # Halted

      most_left_pos = min(most_left_pos, sim.tape.position)
      most_right_pos = max(most_right_pos, sim.tape.position)
      if sim.state == init_state:
        offset = sim.tape.position - init_pos
        if offset > 0:  # Right
          if are_half_tapes_equal(init_tape, most_left_pos,
                                  sim.tape, most_left_pos + offset, dir_offset=+1):
            # print "lin_search", init_step_num, sim.step_num, sim.state, offset, most_left_pos - init_pos
            return Lin_Recur_Result(
              True, init_step=init_step_num,
              period=sim.step_num - init_step_num, offset=offset,
              states_used=states_used, states_last_seen=states_last_seen)
        elif offset < 0:  # Left
          if are_half_tapes_equal(init_tape, most_right_pos,
                                  sim.tape, most_right_pos + offset, dir_offset=-1):
            # print "lin_search", init_step_num, sim.step_num, sim.state, offset, most_right_pos - init_pos
            return Lin_Recur_Result(
              True, init_step=init_step_num,
              period=sim.step_num - init_step_num, offset=offset,
              states_used=states_used, states_last_seen=states_last_seen)
        else:  # In place
          if are_sections_equal(init_tape, sim.tape,
                                most_left_pos, most_right_pos, offset):
            # print "lin_search", init_step_num, sim.step_num, sim.state, offset, most_left_pos - init_pos
            return Lin_Recur_Result(
              True, init_step=init_step_num,
              period=sim.step_num - init_step_num, offset=offset,
              states_used=states_used, states_last_seen=states_last_seen)

  return Lin_Recur_Result(False)  # Give up, ran too long.

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
  parser.add_argument("--max-steps", type=int)
  args = parser.parse_args()

  ttable = IO.load_TTable_filename(args.tm_file, args.tm_line)
  result = lin_search(ttable, max_steps=args.max_steps)
  if result.success:
    # NOTE: result.init_step is not necessarily the earliest time that recurrence
    # starts, it is simply a time after which recurrence is in effect.

    # Do a second search, now that we know the recurrence period to find the
    # earliest start time of the recurrence.
    recur_start = period_search(ttable, result.init_step, result.period)

    print("Found Lin Recurrence: Start:", recur_start, "Period:", result.period, "States used:", sorted(result.states_used))
  else:
    print("No Lin Recurrence found searching up to step", args.max_steps)

if __name__ == "__main__":
  main()
