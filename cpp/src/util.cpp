#include "util.h"

#include <chrono>


namespace busy_beaver {

Timer::Timer() : start_time_(std::chrono::system_clock::now()) {}
void Timer::restart_timer() { start_time_ = std::chrono::system_clock::now(); }

double Timer::time_elapsed_s() const {
  const auto end_time = std::chrono::system_clock::now();
  std::chrono::duration<double> diff = end_time - start_time_;
  return diff.count();
}

char* NowTimestamp() {
  const auto start_time = std::chrono::system_clock::now();
  const std::time_t start_time_t = std::chrono::system_clock::to_time_t(start_time);
  return std::ctime(&start_time_t);
}

}  // namespace busy_beaver
