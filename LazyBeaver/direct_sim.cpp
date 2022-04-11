// Continue enumeration from a file of partially enumerated TMs.

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#include "turing_machine.h"
#include "util.h"


namespace lazy_beaver {

TuringMachine* ReadTM(const std::string& filename, const long line_num) {
  std::ifstream instream(filename, std::ios::in);
  for (long i = line_num; i > 1; i -= 1) {
    std::string line;
    std::getline(instream, line);
  }
  return lazy_beaver::ReadTuringMachine(&instream, "");
}

void DirectSimMain(const std::string& tm_filename, const long line_num,
                   const long num_steps) {
  std::unique_ptr<TuringMachine> tm(lazy_beaver::ReadTM(tm_filename, line_num));

  std::cout << "Starting simulation" << std::endl;
  Timer timer;
  auto result = DirectSimulate(*tm, num_steps);

  std::cout << "Simulated " << result.num_steps
            << " in " << timer.time_elapsed_s() << "s" << std::endl;
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: direct_sim tm_file line_num num_steps" << std::endl;
    return 1;
  } else {
    const std::string tm_filename(argv[1]);
    const long line_num = std::stol(argv[2]);
    const long num_steps = std::stol(argv[3]);

    lazy_beaver::DirectSimMain(tm_filename, line_num, num_steps);

    return 0;
  }
}
