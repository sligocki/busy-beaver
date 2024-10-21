// Run DirectSimulator for a specified number of steps.

#include <iostream>
#include <memory>
#include <string>

#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void DirectSimMain(const std::string& tm_filename, const long line_num,
                   const long num_steps) {
  std::unique_ptr<TuringMachine> tm(
    ReadTuringMachineFile(tm_filename, line_num));

  std::cout << "Starting simulation" << std::endl;
  Timer timer;
  DirectSimulator sim(*tm);
  sim.Seek(num_steps);

  std::cout << "Simulated " << sim.step_num()
            << " in " << timer.time_elapsed_s() << "s" << std::endl;
  if (sim.is_halted()) {
    std::cout << "Halted at step " << sim.step_num() << std::endl;
  }
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: direct_sim tm_file line_num num_steps" << std::endl;
    return 1;
  } else {
    const std::string tm_filename(argv[1]);
    const long line_num = std::stol(argv[2]);
    const long num_steps = std::stol(argv[3]);

    busy_beaver::DirectSimMain(tm_filename, line_num, num_steps);

    return 0;
  }
}
