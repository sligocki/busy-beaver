#include "lin_recur.h"

#include "simulator.h"
#include "turing_machine.h"

namespace lazy_beaver {

LinRecurResult LinRecurDetect(const TuringMachine& tm, const long max_steps) {
  DirectSimulator sim(tm);
  // TODO: states_last_seen = {sim.state: sim.step_num}
  sim.Step();

  while (sim.step_num() < max_steps) {
    const long init_step_num = sim.step_num();
    const long steps_reset = 2 * init_step_num;
    const long init_pos = sim.position();
    const State init_state = sim.state();
    const std::vector<Symbol> init_tape = sim.tape();
    long most_left_pos = init_pos;
    long most_right_pos = init_pos;
    // TODO: states_used = set()
    while (sim.step_num() < max_steps) {
      // states_last_seen[sim.state] = sim.step_num
      // states_used.add(sim.state)
      sim.Step();
      if (sim.is_halted()) {
        return {true, false, 0, 0, 0};
      }

      most_left_pos = std::min(most_left_pos, sim.position());
      most_right_pos = std::max(most_left_pos, sim.position());
      if (sim.state() == init_state) {
        long offset = sim.position() - init_pos;
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
                                 most_left_pos, most_right_pos, offset)) {
            success = true;
          }
        }

        if (success) {
          const long period = sim.step_num() - init_step_num;
          return {false, true, init_step_num, period, offset};
        }
      }
    }
  }

  // Neither halting nor LR detected.
  return {false, false, 0, 0, 0};
}

}  // namespace lazy_beaver
