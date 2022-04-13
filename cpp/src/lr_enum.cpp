// Enumerate TMs using Lin Recurence (and Direct Simulation) to quickly cull the
// vast majority which halt / enter Lin Recurence within say 100 steps.

#include <fstream>
#include <iostream>
#include <string>

#include "enumerator.h"
#include "lin_recur.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

class LinRecurEnum : public BaseEnumerator {
 public:
  LinRecurEnum(const bool allow_no_halt,
               const long max_steps,
               const std::string& out_inf_filename,
               const std::string& out_nonhalt_filename);

  virtual ~LinRecurEnum();

  void print_stats() const;

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm);

  const long max_steps_;

  // Output streams
  std::ofstream out_inf_stream_;
  std::ofstream out_unknown_stream_;

  // Stats
  Timer timer_;
  Timer last_print_;
  long num_tms_total_ = 0;
  long num_tms_halt_ = 0;
  long num_tms_inf_ = 0;
  long num_tms_unknown_ = 0;

  long max_period_ = 0;
  std::unique_ptr<TuringMachine> max_period_tm_;
};

LinRecurEnum::LinRecurEnum(const bool allow_no_halt,
                           const long max_steps,
                           const std::string& out_inf_filename,
                           const std::string& out_unknown_filename)
  : BaseEnumerator(allow_no_halt),
    max_steps_(max_steps),
    out_inf_stream_(out_inf_filename, std::ios::out | std::ios::binary),
    out_unknown_stream_(out_unknown_filename, std::ios::out | std::ios::binary) {
}

LinRecurEnum::~LinRecurEnum() {
  out_unknown_stream_.close();
}

void LinRecurEnum::print_stats() const {
  std::cout << "TMs:  Total: " << num_tms_total_
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
    print_stats();
    last_print_.restart_timer();
  }

  auto result = LinRecurDetect(tm, max_steps_);

  num_tms_total_ += 1;
  if (result.is_halted) {
    num_tms_halt_ += 1;
  } else if (result.is_lin_recurrent) {
    num_tms_inf_ += 1;
    // Write TM that entered Lin Recurence allong with it's period, etc.
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


void LinRecurEnumerate(
    const int num_states, const int num_symbols,
    const long max_steps, const bool allow_no_halt, const bool first_1rb,
    const std::string& out_inf_filename,
    const std::string& out_unknown_filename) {
  std::cout << "Start: " << num_states << "x" << num_symbols << std::endl;

  // Depth-first search of all TMs in TNF.
  LinRecurEnum enumerator(allow_no_halt, max_steps,
                          out_inf_filename, out_unknown_filename);
  std::unique_ptr<TuringMachine> init_tm(
    new TuringMachine(num_states, num_symbols));
  if (first_1rb) {
    const TuringMachine::LookupResult next = {1, +1, 1};  // 1RB
    init_tm.reset(new TuringMachine(
      *init_tm, InitialState, BlankSymbol, next, 0));
  }
  enumerator.enumerate(init_tm.release());

  enumerator.print_stats();
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 6) {
    std::cerr << "Usage: lr_enum num_states num_symbols max_steps out_inf_file out_unknwon_file" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_inf_filename(argv[4]);
    const std::string out_unknown_filename(argv[5]);

    // TODO: Allow configuring allow_no_halt and first_1rb.
    busy_beaver::LinRecurEnumerate(num_states, num_symbols, max_steps,
                                   true, true,
                                   out_inf_filename, out_unknown_filename);
  }
}
