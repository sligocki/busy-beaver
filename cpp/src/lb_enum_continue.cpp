// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <map>
#include <string>

#include "enumeration.h"
#include "turing_machine.h"


namespace lazy_beaver {

void ContinueEnumerateFromFile(std::ifstream* in_stack_stream,
                               std::ifstream* in_steps_stream,
                               const long max_steps,
                               std::ofstream* out_steps_example_stream,
                               std::ofstream* save_stack_stream,
                               int proc_num,
                               std::string stop_name) {
  std::stack<TuringMachine*> tms;

  for (int i = 0;; ++i) {
    // For now, we use a dummy base name for TMs which is just the "(4)" for
    // the TM 4 in the file.
    std::string tm_base_name("(");
    tm_base_name.append(std::to_string(i));
    tm_base_name.append(")");
    lazy_beaver::TuringMachine* tm = lazy_beaver::ReadTuringMachine(in_stack_stream, tm_base_name);
    if (tm == nullptr) {
      break;
    } else {
      tms.push(tm);
    }
  }

  std::set<long> steps_run;
  if (in_steps_stream->is_open())
  {
    std::string in_steps_line;
    while (std::getline(*in_steps_stream, in_steps_line)) {
      long in_steps = std::stol(in_steps_line);
      steps_run.insert(in_steps);
    }
  }

  Enumerate(&tms, max_steps, &steps_run, out_steps_example_stream, nullptr, save_stack_stream, proc_num, stop_name);
  // Enumerate(&tms, max_steps, &steps_run, nullptr, nullptr, save_stack_stream, proc_num);
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc < 6) {
    std::cerr << "Usage: continue_enum in_tm_file max_steps out_steps_example_file save_stack_file proc_num" << std::endl;
    return 1;
  } else {
    const std::string in_stack_filename(argv[1]);
    std::ifstream in_stack_stream(in_stack_filename, std::ios::in);

    const long max_steps = std::stol(argv[2]);

    std::ofstream out_steps_example_stream(argv[3], std::ios::out | std::ios::binary);

    std::ofstream save_stack_stream(argv[4], std::ios::out | std::ios::binary);

    int proc_num = std::stoi(argv[5]);

    std::string stop_name = "stop.enumeration";
    if (argc > 6) {
      stop_name = argv[6];
    }

    std::ifstream in_steps_stream;
    if (argc > 7) {
      const std::string in_steps_filename(argv[7]);
      in_steps_stream.open(in_steps_filename, std::ios::in);
    }

    lazy_beaver::ContinueEnumerateFromFile(&in_stack_stream, &in_steps_stream, max_steps, &out_steps_example_stream, &save_stack_stream, proc_num, stop_name);
    // lazy_beaver::ContinueEnumerateFromFile(&in_stack_stream, &in_steps_stream, max_steps, nullptr, &save_stack_stream, proc_num);

    in_stack_stream.close();
    in_steps_stream.close();

    out_steps_example_stream.close();
    save_stack_stream.close();

    return 0;
  }
}
