// Run DirectSimulator for a specified number of steps.

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
    ReadTuringMachine(tm_filename, line_num));

  std::cout << "Running Lin Recur Detection" << std::endl;
  Timer timer;
  auto result = LinRecurDetect(*tm, max_steps);

  std::cout << "Finished Lin Recur Detection in "
            << timer.time_elapsed_s() << "s" << std::endl;
  std::cout << "is_halted: " << result.is_halted << std::endl;
  std::cout << "is_lin_recurrent: " << result.is_lin_recurrent << std::endl;
  if (result.is_lin_recurrent) {
    std::cout << "start_step: " << result.lr_start_step << std::endl;
    std::cout << "period: " << result.lr_period << std::endl;
    std::cout << "offset: " << result.lr_offset << std::endl;
  }
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: lin_recur tm_file line_num max_steps" << std::endl;
    return 1;
  } else {
    const std::string tm_filename(argv[1]);
    const long line_num = std::stol(argv[2]);
    const long max_steps = std::stol(argv[3]);

    busy_beaver::LinRecurMain(tm_filename, line_num, max_steps);

    return 0;
  }
}
