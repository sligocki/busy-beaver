#include "lin_recur_enumerator.h"

#include <fstream>
#include <iostream>
#include <string>

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
                           const std::string& proc_id)
  : BaseEnumerator(allow_no_halt),
    max_steps_(max_steps),
    out_halt_stream_(out_halt_filename, std::ios::out | std::ios::binary),
    out_inf_stream_(out_inf_filename, std::ios::out | std::ios::binary),
    out_unknown_stream_(out_unknown_filename, std::ios::out | std::ios::binary),
    proc_id_(proc_id) {
}

LinRecurEnum::~LinRecurEnum() {
  out_unknown_stream_.close();
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
    // TODO: If writing Halting TMs. Add the halt state.
    WriteTuringMachine(tm, &out_halt_stream_);
  } else if (result.is_lin_recurrent) {
    num_tms_inf_ += 1;
    // Write TM that entered Lin Recurence along with it's period, etc.
    WriteTuringMachine(tm, &out_inf_stream_);
    out_inf_stream_ << " | Lin_Recur " << result.lr_period << " "
                    << result.lr_offset << " <" << result.lr_start_step << std::endl;
    if (result.lr_period > max_period_) {
      max_period_ = result.lr_period;
      max_period_tm_.reset(new TuringMachine(tm));
    }
  } else {
    num_tms_unknown_ += 1;
    WriteTuringMachine(tm, &out_unknown_stream_);
    out_unknown_stream_ << std::endl;
  }

  // Data needed for enumeration expansion.
  return {result.is_halted, result.last_state, result.last_symbol};
}

}  // namespace busy_beaver
