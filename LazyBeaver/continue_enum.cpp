// Prototype script for quickly calculating Lazy Beaver by enumerating
// candidates and directly simulating them on an uncomressed tape.

#include <fstream>
#include <iostream>
#include <string>

#include "enumeration.h"
#include "turing_machine.h"


int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: continue_enum tm_file" << std::endl;
    return 1;
  } else {
    const std::string infilename(argv[1]);
    std::ifstream instream(infilename, std::ios::in);

    lazy_beaver::TuringMachine* tm;
    while ((tm = lazy_beaver::ReadTuringMachine(&instream)) != nullptr) {
      lazy_beaver::WriteTuringMachine(*tm, &std::cout);
    }

    return 0;
  }
}
