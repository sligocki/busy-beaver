// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <map>
#include <string>

#include "enumeration.h"
#include "turing_machine.h"


namespace lazy_beaver {

void ContinueEnumerateFromFile(std::istream* instream, const long max_steps,
                               std::ostream* out_steps_example_stream) {
  std::stack<TuringMachine*> tms;
  lazy_beaver::TuringMachine* tm;
  while ((tm = lazy_beaver::ReadTuringMachine(instream)) != nullptr) {
    tms.push(tm);
  }
  std::map<long, TuringMachine*> steps_example;
  Enumerate(&tms, max_steps, &steps_example);

  // Write all steps examples to a file.
  for (const auto& [steps, tm] : steps_example) {
    *out_steps_example_stream << steps << "\t";
    WriteTuringMachine(*tm, out_steps_example_stream);
  }
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: continue_enum in_tm_file max_steps out_steps_example_file" << std::endl;
    return 1;
  } else {
    const std::string infilename(argv[1]);
    std::ifstream instream(infilename, std::ios::in);
    const long max_steps = std::stol(argv[2]);
    std::ofstream out_steps_example_stream(argv[3], std::ios::out | std::ios::binary);

    lazy_beaver::ContinueEnumerateFromFile(&instream, max_steps, &out_steps_example_stream);

    out_steps_example_stream.close();

    return 0;
  }
}
