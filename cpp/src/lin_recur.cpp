#include "lin_recur.h"

#include <iostream>

#include "simulator.h"
#include "turing_machine.h"


namespace busy_beaver {

namespace {

bool are_half_tapes_equal(const Tape& tape1, const long start_pos1,
                          const Tape& tape2, const long start_pos2,
                          const long dir_offset) {
  long pos1 = start_pos1;
  long pos2 = start_pos2;
  while (tape1.in_range(pos1) || tape2.in_range(pos2)) {
    if (tape1.read(pos1) != tape2.read(pos2)) {
      return false;
    }
    pos1 += dir_offset;
    pos2 += dir_offset;
  }
  // Entire half-tapes are equal!
  return true;
}

bool are_sections_equal(
    const Tape& start_tape, const Tape& end_tape,
    const long most_left_pos, const long most_right_pos) {
  for (long pos = most_left_pos; pos <= most_right_pos; pos += 1) {
    if (start_tape.read(pos) != end_tape.read(pos)) {
      return false;
    }
  }
  return true;
}

}  // namespace

LinRecurResult LinRecurDetect(const TuringMachine& tm, const long max_steps) {
  DirectSimulator sim(tm);
  // TODO: states_last_seen = {sim.state: sim.step_num}
  // TODO: Consider Seek(1024) or something like this to avoid lots of early copies.
  sim.Step();

  while (sim.step_num() < max_steps) {
    const long init_step_num = sim.step_num();
    const long steps_reset = 2 * init_step_num;
    const State init_state = sim.state();
    const Tape init_tape = sim.tape();
    const long init_pos = init_tape.position();
    long most_left_pos = init_pos;
    long most_right_pos = init_pos;
    // TODO: states_used = set()
    while (sim.step_num() < steps_reset) {
      // states_last_seen[sim.state] = sim.step_num
      // states_used.add(sim.state)
      sim.Step();
      if (sim.is_halted()) {
        return {true, false, 0, 0, 0, sim.last_state(), sim.last_symbol()};
      }

      most_left_pos = std::min(most_left_pos, sim.tape().position());
      most_right_pos = std::max(most_right_pos, sim.tape().position());
      if (sim.state() == init_state) {
        long offset = sim.tape().position() - init_pos;
        bool success = false;
        if (offset > 0) {  // Right
          if (are_half_tapes_equal(init_tape, most_left_pos,
                                   sim.tape(), most_left_pos + offset,
                                   +1)) {
            success = true;
          }
        } else if (offset < 0) {  // Left
          if (are_half_tapes_equal(init_tape, most_right_pos,
                                   sim.tape(), most_right_pos + offset,
                                   -1)) {
            success = true;
          }
        } else {  // In place
          if (are_sections_equal(init_tape, sim.tape(),
                                 most_left_pos, most_right_pos)) {
            success = true;
          }
        }

        if (success) {
          const long period = sim.step_num() - init_step_num;
          return {false, true, init_step_num, period, offset, 0, 0};
        }
      }
    }
  }

  // Neither halting nor LR detected.
  return {false, false, 0, 0, 0, 0, 0};
}

}  // namespace busy_beaver
