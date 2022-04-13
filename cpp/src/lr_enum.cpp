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
               const std::string& out_nonhalt_filename);

  virtual ~LinRecurEnum();

  void print_stats(const TuringMachine* tm = nullptr) const;

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm);

  const long max_steps_;

  // Output streams
  std::ofstream out_stream_;

  // Stats
  long num_tms_total_ = 0;
  long num_tms_halt_ = 0;
  long num_tms_inf_ = 0;
  long num_tms_unknown_ = 0;
};

LinRecurEnum::LinRecurEnum(const bool allow_no_halt,
                           const long max_steps,
                           const std::string& out_filename)
  : BaseEnumerator(allow_no_halt),
    max_steps_(max_steps),
    out_stream_(out_filename, std::ios::out | std::ios::binary) {
}

LinRecurEnum::~LinRecurEnum() {
  out_stream_.close();
}

void LinRecurEnum::print_stats(const TuringMachine* tm) const {
  std::cout << "TMs: Total: " << num_tms_total_
            << " Halt: " << num_tms_halt_
            << " Infinite: " << num_tms_inf_
            << " Unknown: " << num_tms_unknown_;
  if (tm) {
    std::cout << " TM: " << tm->hereditary_name() << " / ";
    WriteTuringMachine(*tm, &std::cout);
  }
  std::cout << std::endl;
}

EnumExpandParams LinRecurEnum::filter_tm(const TuringMachine& tm) {
  if ((num_tms_total_ % 10000000) == 0) {
    print_stats(&tm);
  }

  auto result = LinRecurDetect(tm, max_steps_);

  num_tms_total_ += 1;
  if (result.is_halted) {
    num_tms_halt_ += 1;
  } else if (result.is_lin_recurrent) {
    num_tms_inf_ += 1;
  } else {
    num_tms_unknown_ += 1;
    WriteTuringMachine(tm, &out_stream_);
  }

  // Data needed for enumeration expansion.
  return {result.is_halted, result.last_state, result.last_symbol};
}


void LinRecurEnumerate(
    const int num_states, const int num_symbols,
    const long max_steps, const bool allow_no_halt,
    const std::string& out_filename) {
  Timer timer;
  std::cout << "Start: " << num_states << "x" << num_symbols << std::endl;

  // Depth-first search of all TMs in TNF.
  LinRecurEnum enumerator(allow_no_halt, max_steps, out_filename);
  enumerator.enumerate(new TuringMachine(num_states, num_symbols));

  enumerator.print_stats();
  std::cout << "Finished in " << timer.time_elapsed_s() << "s" << std::endl;
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 5) {
    std::cerr << "Usage: lr_enum num_states num_symbols max_steps out_file" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_filename(argv[4]);

    // TODO: Allow configuring allow_no_halt.
    busy_beaver::LinRecurEnumerate(num_states, num_symbols, max_steps, true,
                                   out_filename);
  }
}
