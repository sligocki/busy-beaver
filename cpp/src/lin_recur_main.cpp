// Run Lin Recurrence check on a single TM.

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#include "lin_recur.h"
#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void LinRecurMain(const std::string& tm_filename, const long line_num,
                  const long max_steps) {
  std::unique_ptr<TuringMachine> tm(
    ReadTuringMachineFile(tm_filename, line_num));

  std::cout << "Running Lin Recur Detection" << std::endl;
  Timer timer;
  auto result = LinRecurDetect(*tm, max_steps);

  if (result.is_lin_recurrent) {
    std::cout << "Lin Recurrence Detected" << std::endl;
    std::cout << "  start_step: " << result.lr_start_step << std::endl;
    std::cout << "  period: " << result.lr_period << std::endl;
    std::cout << "  offset: " << result.lr_offset << std::endl;
  } else if (result.is_halted) {
    std::cout << "Halted" << std::endl;
    std::cout << "  steps_run: " << result.steps_run << std::endl;
    std::cout << "  sigma_score: " << result.sigma_score << std::endl;
    std::cout << "  last_state: " << result.last_state << std::endl;
    std::cout << "  last_symbol: " << result.last_symbol << std::endl;
  } else {
    std::cout << "Inconclusive" << std::endl;
    std::cout << "  steps_run: " << result.steps_run << std::endl;
    std::cout << "  max_ref_config_step: " << result.max_ref_config_step << std::endl;
  }
  std::cout << "Runtime: " << timer.time_elapsed_s() << "s" << std::endl;
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: lin_recur tm_file line_num log2(max_steps)" << std::endl;
    return 1;
  } else {
    const std::string tm_filename(argv[1]);
    const long line_num = std::stol(argv[2]);
    const long log2_max_steps = std::stol(argv[3]);
    const long max_steps = 1L << log2_max_steps;  // 2^log2_max_steps

    busy_beaver::LinRecurMain(tm_filename, line_num, max_steps);

    return 0;
  }
}
