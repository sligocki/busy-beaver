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
    const std::string& out_halt_filename,
    const std::string& out_inf_filename,
    const std::string& out_unknown_filename,
    const bool compress_output) {
  std::cout << "Start: " << num_states << "x" << num_symbols << std::endl;
  // Depth-first search of all TMs in TNF.
  LinRecurEnum enumerator(allow_no_halt, max_steps,
                          out_halt_filename, out_inf_filename,
                          out_unknown_filename,
                          /* proc_id = */ "",
                          compress_output);
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
  if (argc < 8 || argc > 9) {
    std::cerr << "Usage: lr_enum num_states num_symbols max_steps out_halt_filename out_inf_file out_unknown_file allow_no_halt [compress_output]" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_halt_filename(argv[4]);
    const std::string out_inf_filename(argv[5]);
    const std::string out_unknown_filename(argv[6]);
    const std::string allow_no_halt_str(argv[7]);
    std::string compress_output_str("false");

    if (argc == 9) {
      compress_output_str = argv[8];
    }

    bool allow_no_halt;
    if (allow_no_halt_str == "true") {
      allow_no_halt = true;
    } else if (allow_no_halt_str == "false") {
      allow_no_halt = false;
    } else {
      std::cerr << "allow_no_halt must be true/false not ["
                << allow_no_halt_str << "]" << std::endl;
      return 1;
    }

    bool compress_output;
    if (compress_output_str == "true") {
      compress_output = true;
    } else if (compress_output_str == "false") {
      compress_output = false;
    } else {
      std::cerr << "compress_output must be true/false not ["
                << compress_output_str << "]" << std::endl;
      return 1;
    }

    // TODO: Allow configuring allow_no_halt and first_1rb.
    busy_beaver::LinRecurEnumerate(
      num_states, num_symbols, max_steps,
      allow_no_halt, /* first_1rb = */ true,
      out_halt_filename, out_inf_filename, out_unknown_filename,
      compress_output);
  }
}
