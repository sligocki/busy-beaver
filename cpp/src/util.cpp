#include "util.h"

#include <chrono>


namespace busy_beaver {

Timer::Timer() : start_time_(std::chrono::system_clock::now()) {}
void Timer::restart_timer() { start_time_ = std::chrono::system_clock::now(); }

double Timer::time_elapsed_s() {
  const auto end_time = std::chrono::system_clock::now();
  std::chrono::duration<double> diff = end_time - start_time_;
  return diff.count();
}

}  // namespace busy_beaver
