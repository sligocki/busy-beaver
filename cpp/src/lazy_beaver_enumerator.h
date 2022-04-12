#ifndef BUSY_BEAVER_LAZY_BEAVER_ENUMERATOR_H_
#define BUSY_BEAVER_LAZY_BEAVER_ENUMERATOR_H_

#include <fstream>
#include <memory>
#include <set>
#include <string>

#include "enumerator.h"
#include "turing_machine.h"


namespace busy_beaver {

class LazyBeaverEnum : public BaseEnumerator {
 public:
  LazyBeaverEnum(const long max_steps,
                 const std::string& out_witness_filename,
                 const std::string& out_nonhalt_filename,
                 const std::string& print_prefix = "");

  virtual ~LazyBeaverEnum();

  // Find minimum non-realized step count (Lazy Beaver value).
  long min_missing() const;

  void print_stats() const;

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm);

  const long max_steps_;
  // Set of all step counts that are realized by a TM.
  std::set<long> steps_realized_;

  // Output streams
  std::unique_ptr<std::ofstream> out_witness_stream_;
  std::unique_ptr<std::ofstream> out_nonhalt_stream_;

  // Stats
  std::string print_prefix_;
  long num_tms_total_ = 0;
  long num_tms_halt_ = 0;
};

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_ENUMERATOR_H_
