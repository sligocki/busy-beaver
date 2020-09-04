// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <string>

#include "enumeration.h"
#include "turing_machine.h"


namespace lazy_beaver {

void ContinueEnumerateFromFile(std::istream* instream, const long max_steps) {
  std::stack<TuringMachine*> tms;
  lazy_beaver::TuringMachine* tm;
  while ((tm = lazy_beaver::ReadTuringMachine(instream)) != nullptr) {
    tms.push(tm);
  }
  Enumerate(&tms, max_steps);
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc != 3) {
    std::cerr << "Usage: continue_enum tm_file max_steps" << std::endl;
    return 1;
  } else {
    const std::string infilename(argv[1]);
    std::ifstream instream(infilename, std::ios::in);
    const long max_steps = std::stol(argv[2]);

    lazy_beaver::ContinueEnumerateFromFile(&instream, max_steps);
    return 0;
  }
}
