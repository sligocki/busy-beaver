#ifndef BUSY_BEAVER_LIN_RECUR_ENUMERATOR_H_
#define BUSY_BEAVER_LIN_RECUR_ENUMERATOR_H_

#include <fstream>
#include <iostream>
#include <string>

#include "enumerator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

class LinRecurEnum : public BaseEnumerator {
 public:
  LinRecurEnum(const bool allow_no_halt,
               const long max_steps,
               const std::string& out_inf_filename,
               const std::string& out_nonhalt_filename,
               const std::string& proc_id = "");

  virtual ~LinRecurEnum();

  void print_stats() const;

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm);

  const long max_steps_;

  // Output streams
  std::ofstream out_inf_stream_;
  std::ofstream out_unknown_stream_;

  // Stats
  const std::string proc_id_;
  Timer timer_;
  Timer last_print_;
  long num_tms_total_ = 0;
  long num_tms_halt_ = 0;
  long num_tms_inf_ = 0;
  long num_tms_unknown_ = 0;

  long max_period_ = 0;
  std::unique_ptr<TuringMachine> max_period_tm_;
};

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_LIN_RECUR_ENUMERATOR_H_
