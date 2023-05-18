#include "lin_recur_enumerator.h"

#include <fstream>
#include <iostream>
#include <ostream>
#include <string>

#ifdef BOOST_FOUND
#include <boost/iostreams/filtering_streambuf.hpp>
#include <boost/iostreams/copy.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#endif

#include "enumerator.h"
#include "lin_recur.h"
#include "turing_machine.h"
#include "util.h"

namespace busy_beaver {

LinRecurEnum::LinRecurEnum(const bool allow_no_halt,
                           const long max_steps,
                           const std::string& out_halt_filename,
                           const std::string& out_inf_filename,
                           const std::string& out_unknown_filename,
                           const std::string& proc_id,
                           const bool compress_output,
                           const bool only_unknown_in)
  : BaseEnumerator(allow_no_halt),
#ifdef BOOST_FOUND
    out_halt_stream_   (&out_halt_buf_),
    out_inf_stream_    (&out_inf_buf_),
    out_unknown_stream_(&out_unknown_buf_),
#endif
    max_steps_(max_steps),
    proc_id_(proc_id)
{
#ifdef BOOST_FOUND
  std::string file_suffix = "";

  if (compress_output) {
    file_suffix = ".gz";
  }

  only_unknown = only_unknown_in;

  out_halt_stream_2_   .open(out_halt_filename    + file_suffix, std::ios::out | std::ios::binary);
  out_inf_stream_2_    .open(out_inf_filename     + file_suffix, std::ios::out | std::ios::binary);
  out_unknown_stream_2_.open(out_unknown_filename + file_suffix, std::ios::out | std::ios::binary);

  if (compress_output) {
    out_halt_buf_   .push(boost::iostreams::gzip_compressor());
    out_inf_buf_    .push(boost::iostreams::gzip_compressor());
    out_unknown_buf_.push(boost::iostreams::gzip_compressor());
  }

  out_halt_buf_   .push(out_halt_stream_2_);
  out_inf_buf_    .push(out_inf_stream_2_);
  out_unknown_buf_.push(out_unknown_stream_2_);
#else
  if (compress_output) {
    std::cerr << "Compressing TM output without compiling with Boost isn't supported\n";
    std::exit(1);
  }

  out_halt_stream_.open(out_halt_filename, std::ios::out | std::ios::binary);
  out_inf_stream_.open(out_inf_filename, std::ios::out | std::ios::binary);
  out_unknown_stream_.open(out_unknown_filename, std::ios::out | std::ios::binary);
#endif
}

LinRecurEnum::~LinRecurEnum() {
#if BOOST_FOUND
  boost::iostreams::close(out_halt_buf_   );
  boost::iostreams::close(out_inf_buf_    );
  boost::iostreams::close(out_unknown_buf_);

  out_halt_stream_2_   .close();
  out_inf_stream_2_    .close();
  out_unknown_stream_2_.close();
#else
  out_halt_stream_   .close();
  out_inf_stream_    .close();
  out_unknown_stream_.close();
#endif
}

void LinRecurEnum::print_stats(const std::string& prefix) const {
  std::cout << prefix << " " << proc_id_ << ": Total: " << num_tms_total_
            << "  Halt: " << num_tms_halt_
            << "  Infinite: " << num_tms_inf_
            << "  Unknown: " << num_tms_unknown_
            << "  Max Period: " << max_period_ << " : ";
  if (max_period_tm_) {
    WriteTuringMachine(*max_period_tm_, &std::cout);
  }
  std::cout << " (" << timer_.time_elapsed_s() << "s)" << std::endl;
}

EnumExpandParams LinRecurEnum::filter_tm(const TuringMachine& tm) {
  if (last_print_.time_elapsed_s() > 60.0) {
    print_stats("Progress");
    last_print_.restart_timer();
  }

  auto result = LinRecurDetect(tm, max_steps_);

  num_tms_total_ += 1;
  if (result.is_halted) {
    num_tms_halt_ += 1;
    
    if (!only_unknown) {
      // TODO: If writing Halting TMs. Add the halt state.
      WriteTuringMachine(tm, &out_halt_stream_);
      out_halt_stream_ << " | Halt " << result.steps_run << "\n";
    }
  } else if (result.is_lin_recurrent) {
    num_tms_inf_ += 1;

    if (!only_unknown) {
      // Write TM that entered Lin Recurence along with it's period, etc.
      WriteTuringMachine(tm, &out_inf_stream_);
      out_inf_stream_ << " | Lin_Recur " << result.lr_period << " "
                       << result.lr_offset << " <" << result.lr_start_step << "\n";
      if (result.lr_period > max_period_) {
        max_period_ = result.lr_period;
        max_period_tm_.reset(new TuringMachine(tm));
      }
    }
  } else {
    num_tms_unknown_ += 1;

    WriteTuringMachine(tm, &out_unknown_stream_);
    out_unknown_stream_ << "\n";
  }

  // Data needed for enumeration expansion.
  return {result.is_halted, result.last_state, result.last_symbol};
}

}  // namespace busy_beaver
