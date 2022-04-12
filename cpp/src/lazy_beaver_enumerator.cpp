#include "lazy_beaver_enumerator.h"

#include <fstream>
#include <iostream>
#include <set>
#include <string>

#include "enumerator.h"
#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

LazyBeaverEnum::LazyBeaverEnum(const long max_steps,
                               const std::string& out_witness_filename,
                               const std::string& out_nonhalt_filename,
                               const std::string& print_prefix)
  : BaseEnumerator(/* allow_no_halt = */ false),
    max_steps_(max_steps),
    print_prefix_(print_prefix) {
  out_witness_stream_.reset(
    new std::ofstream(out_witness_filename, std::ios::out | std::ios::binary));
  if (!out_nonhalt_filename.empty()) {
    out_nonhalt_stream_.reset(
      new std::ofstream(out_nonhalt_filename, std::ios::out | std::ios::binary));
  }
}

LazyBeaverEnum::~LazyBeaverEnum() {
  out_witness_stream_->close();
  if (out_nonhalt_stream_) {
    out_nonhalt_stream_->close();
  }
}

long LazyBeaverEnum::min_missing() const {
  for (long i = 1;; ++i) {
    if (steps_realized_.count(i) == 0) {
      return i;
    }
  }
}

void LazyBeaverEnum::print_stats() const {
  std::cout << "Stat " << print_prefix_
            << ": # TMs simulated = " << num_tms_total_ << std::endl;
  std::cout << "Stat " << print_prefix_
            << ": # TMs halted = " << num_tms_halt_ << std::endl;
}

EnumExpandParams LazyBeaverEnum::filter_tm(const TuringMachine& tm) {
  if ((num_tms_total_ % 10000000) == 0) {
      std::cout << "Progress " << print_prefix_ << ":"
                << " TMs simulated: " << num_tms_total_
                << " Provisional LB: " << min_missing()
                << " Current TM hereditary_order: " << tm.hereditary_name()
                << std::endl;
  }

  DirectSimulator sim(tm);
  sim.Seek(max_steps_);

  num_tms_total_ += 1;
  if (sim.is_halted()) {
    num_tms_halt_ += 1;
    if (steps_realized_.count(sim.step_num()) == 0) {
      // Log this TM
      steps_realized_.insert(sim.step_num());

      // Write witness
      *out_witness_stream_ << sim.step_num() << "\t";
      WriteTuringMachine(tm, out_witness_stream_.get());
    }
  } else {
    // Non-halting machine.
    if (out_nonhalt_stream_) {
      WriteTuringMachine(tm, out_nonhalt_stream_.get());
    }
  }

  // Data needed for enumeration expansion.
  return {sim.is_halted(), sim.last_state(), sim.last_symbol()};
}

}  // namespace busy_beaver
