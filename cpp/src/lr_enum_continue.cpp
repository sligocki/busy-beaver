// Enumerate TMs using Lin Recurence (and Direct Simulation) to quickly cull the
// vast majority which halt / enter Lin Recurence within say 100 steps.

#include <iostream>
#include <string>

#include "enumerator.h"
#include "lin_recur_enumerator.h"
#include "turing_machine.h"


namespace busy_beaver {

void ContinueLinRecurEnumerate(
    const std::string& in_tms_filename, const long max_steps,
    const bool allow_no_halt, const bool first_1rb,
    const std::string& out_halt_filename,
    const std::string& out_inf_filename,
    const std::string& out_unknown_filename,
    const std::string& proc_id) {
  std::cout << "Start " << proc_id << std::endl;

  LinRecurEnum enumerator(allow_no_halt, max_steps,
                          out_halt_filename, out_inf_filename,
                          out_unknown_filename, proc_id);

  // Go through all TMs in infile enumerating each (and all children).
  std::ifstream in_tms_stream(in_tms_filename, std::ios::in | std::ios::binary);
  while (true) {
    TuringMachine* tm = ReadTuringMachine(&in_tms_stream, "");
    if (tm == nullptr) {
      break;
    } else {
      // Enumerate each TM (and all children) before moving on to next TM.
      enumerator.enumerate(tm);
    }
  }

  enumerator.print_stats("Final");
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 8) {
    std::cerr << "Usage: lr_enum_continue in_tm_file max_steps out_halt_file out_inf_file out_unknown_file proc_id allow_no_halt" << std::endl;
    return 1;
  } else {
    const std::string in_tms_filename(argv[1]);
    const long max_steps = std::stol(argv[2]);
    const std::string out_halt_filename(argv[3]);
    const std::string out_inf_filename(argv[4]);
    const std::string out_unknown_filename(argv[5]);
    const std::string proc_id(argv[6]);
    const std::string allow_no_halt_str(argv[7]);

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

    // TODO: Allow configuring allow_no_halt and first_1rb.
    busy_beaver::ContinueLinRecurEnumerate(
      in_tms_filename, max_steps,
      allow_no_halt, /* first_1rb = */ true,
      out_halt_filename, out_inf_filename, out_unknown_filename,
      proc_id);
  }
}
