#ifndef BUSY_BEAVER_LIN_RECUR_ENUMERATOR_H_
#define BUSY_BEAVER_LIN_RECUR_ENUMERATOR_H_

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#ifdef BOOST_FOUND
#include <boost/iostreams/filtering_streambuf.hpp>
#endif

#include "enumerator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

class LinRecurEnum : public BaseEnumerator {
 public:
  LinRecurEnum(const bool allow_no_halt,
               const long max_steps,
               const std::string& out_halt_filename,
               const std::string& out_inf_filename,
               const std::string& out_nonhalt_filename,
               const std::string& proc_id,
               const bool compress_output = false,
               const bool only_unknown_in = false);

  virtual ~LinRecurEnum();

  void print_stats(const std::string& prefix) const;

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm);

  const long max_steps_;

  bool only_unknown_;

  // Output streams
  std::ostream out_halt_stream_;
  std::ostream out_inf_stream_;
  std::ostream out_unknown_stream_;

#ifdef BOOST_FOUND
  // Extra output streams for internal use with the "buf_"s below
  std::ofstream out_halt_stream_2_;
  std::ofstream out_inf_stream_2_;
  std::ofstream out_unknown_stream_2_;

  // Buffers used to compress output
  boost::iostreams::filtering_streambuf<boost::iostreams::output> out_halt_buf_;
  boost::iostreams::filtering_streambuf<boost::iostreams::output> out_inf_buf_;
  boost::iostreams::filtering_streambuf<boost::iostreams::output> out_unknown_buf_;
#endif

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
