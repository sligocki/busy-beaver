#ifndef BUSY_BEAVER_UTIL_H_
#define BUSY_BEAVER_UTIL_H_

#include <chrono>


namespace busy_beaver {

class Timer {
 public:
  Timer();
  void restart_timer();

  // Time elapsed_time since Timer was created (or most recent call to
  // restart_timer()) in seconds.
  double time_elapsed_s() const;

 private:
  std::chrono::time_point<std::chrono::system_clock> start_time_;
};

char* NowTimestamp();

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_UTIL_H_
