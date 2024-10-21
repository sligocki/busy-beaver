// Check period and start step for a Lin Recurrent TM.

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#include "lin_recur.h"
#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void LRCheckMain(const std::string& tm_str,
                 const long start_step, const long period) {
  std::unique_ptr<TuringMachine> tm(ReadTuringMachineStr(tm_str));

  Timer timer;
  auto result = LinRecurCheck(*tm, start_step, period);

  if (result.is_lin_recurrent) {
    std::cout << "Success" << std::endl;
    std::cout << "  start_step: " << result.lr_start_step << std::endl;
    std::cout << "  period: " << result.lr_period << std::endl;
    std::cout << "  offset: " << result.lr_offset << std::endl;
  } else {
    std::cout << "Failed" << std::endl;
    std::cout << "  is_halted: " << result.is_halted << std::endl;
    std::cout << "  steps_run: " << result.steps_run << std::endl;
  }
  std::cout << "Runtime: " << timer.time_elapsed_s() << "s" << std::endl;
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: lr_check tm start_step period" << std::endl;
    return 1;
  } else {
    const std::string tm_str(argv[1]);
    const long start_step = std::stol(argv[2]);
    const long period = std::stol(argv[3]);

    busy_beaver::LRCheckMain(tm_str, start_step, period);

    return 0;
  }
}
