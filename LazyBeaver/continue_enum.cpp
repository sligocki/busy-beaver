// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <map>
#include <string>

#include "enumeration.h"
#include "turing_machine.h"


namespace lazy_beaver {

void ContinueEnumerateFromFile(std::istream* instream,
                               const long max_steps,
                               std::ostream* out_steps_example_stream,
                               std::ostream* save_stack_stream,
                               int proc_num) {
  std::stack<TuringMachine*> tms;

  for (int i = 0;; ++i) {
    // For now, we use a dummy base name for TMs which is just the "(4)" for
    // the TM 4 in the file.
    std::string tm_base_name("(");
    tm_base_name.append(std::to_string(i));
    tm_base_name.append(")");
    lazy_beaver::TuringMachine* tm = lazy_beaver::ReadTuringMachine(instream, tm_base_name);
    if (tm == nullptr) {
      break;
    } else {
      tms.push(tm);
    }
  }

  std::set<long> steps_run;
  Enumerate(&tms, max_steps, &steps_run, out_steps_example_stream, nullptr, save_stack_stream, proc_num);
  // Enumerate(&tms, max_steps, &steps_run, nullptr, nullptr, save_stack_stream, proc_num);
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc != 6) {
    std::cerr << "Usage: continue_enum in_tm_file max_steps out_steps_example_file save_stack_file proc_num" << std::endl;
    return 1;
  } else {
    const std::string infilename(argv[1]);
    std::ifstream instream(infilename, std::ios::in);
    const long max_steps = std::stol(argv[2]);
    std::ofstream out_steps_example_stream(argv[3], std::ios::out | std::ios::binary);
    std::ofstream save_stack_stream(argv[4], std::ios::out | std::ios::binary);
    int proc_num = std::stoi(argv[5]);

    lazy_beaver::ContinueEnumerateFromFile(&instream, max_steps, &out_steps_example_stream, &save_stack_stream, proc_num);

    out_steps_example_stream.close();
    save_stack_stream.close();

    return 0;
  }
}
