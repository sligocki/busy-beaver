// Enumerate TMs using Lin Recurence (and Direct Simulation) to quickly cull the
// vast majority which halt / enter Lin Recurence within say 100 steps.

#include <iostream>
#include <string>

#include "enumerator.h"
#include "lin_recur_enumerator.h"
#include "turing_machine.h"


namespace busy_beaver {

void LinRecurEnumerate(
    const int num_states, const int num_symbols, const long max_steps,
    const bool allow_no_halt, const bool first_1rb,
    const std::string& out_inf_filename,
    const std::string& out_unknown_filename) {
  std::cout << "Start: " << num_states << "x" << num_symbols << std::endl;

  // Depth-first search of all TMs in TNF.
  LinRecurEnum enumerator(allow_no_halt, max_steps,
                          out_inf_filename, out_unknown_filename);
  std::unique_ptr<TuringMachine> init_tm(
    new TuringMachine(num_states, num_symbols));
  if (first_1rb) {
    const TuringMachine::LookupResult next = {1, +1, 1};  // 1RB
    init_tm.reset(new TuringMachine(
      *init_tm, InitialState, BlankSymbol, next, 0));
  }
  enumerator.enumerate(init_tm.release());

  enumerator.print_stats("Final");
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 6) {
    std::cerr << "Usage: lr_enum num_states num_symbols max_steps out_inf_file out_unknown_file" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_inf_filename(argv[4]);
    const std::string out_unknown_filename(argv[5]);

    // TODO: Allow configuring allow_no_halt and first_1rb.
    busy_beaver::LinRecurEnumerate(num_states, num_symbols, max_steps,
                                   /* allow_no_halt = */ false,  // TODO: Allow configuring this.
                                   /* first_1rb = */ true,
                                   out_inf_filename, out_unknown_filename);
  }
}
