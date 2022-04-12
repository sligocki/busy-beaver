// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <string>

#include "lazy_beaver_enumerator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void ContinueEnumerateFromFile(const std::string& in_tms_filename,
                               const long max_steps,
                               const std::string& out_witness_filename,
                               const long proc_num) {
  Timer timer;
  LazyBeaverEnum enumerator(max_steps, out_witness_filename, "",
                            std::to_string(proc_num));
  std::ifstream in_tms_stream(in_tms_filename, std::ios::in | std::ios::binary);
  for (int i = 0;; ++i) {
    // For now, we use a dummy base name for TMs which is just the "(4)" for
    // the TM 4 in the file.
    std::string tm_base_name("(");
    tm_base_name.append(std::to_string(i));
    tm_base_name.append(")");
    TuringMachine* tm = ReadTuringMachine(&in_tms_stream, tm_base_name);
    if (tm == nullptr) {
      break;
    } else {
      // Enumerate each TM (and all children) before moving on to next TM.
      enumerator.enumerate(tm);
    }
  }

  enumerator.print_stats();
  std::cout << "Stat : Runtime = " << timer.time_elapsed_s() << std::endl;
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 5) {
    std::cerr << "Usage: continue_enum in_tm_file max_steps out_witness_file proc_num" << std::endl;
    return 1;
  } else {
    const std::string in_tms_filename(argv[1]);
    const long max_steps = std::stol(argv[2]);
    const std::string out_witness_filename(argv[3]);
    const int proc_num = std::stoi(argv[4]);

    busy_beaver::ContinueEnumerateFromFile(
      in_tms_filename, max_steps, out_witness_filename, proc_num);

    return 0;
  }
}
