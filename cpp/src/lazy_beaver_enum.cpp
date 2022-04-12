// Prototype script for quickly calculating Lazy Beaver by enumerating
// candidates and directly simulating them on an uncompressed tape.

#include <fstream>
#include <iostream>
#include <set>
#include <string>

#include "enumerator.h"
#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

class LazyBeaverEnum : public BaseEnumerator {
 public:
  LazyBeaverEnum(const long max_steps,
                 const std::string& out_witness_filename,
                 const std::string& out_nonhalt_filename,
                 const std::string& print_prefix = "")
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

  virtual ~LazyBeaverEnum() {
    out_witness_stream_->close();
    if (out_nonhalt_stream_) {
      out_nonhalt_stream_->close();
    }
  }

  // Find minimum non-realized step count (Lazy Beaver value).
  long min_missing() const {
    for (long i = 1;; ++i) {
      if (steps_realized_.count(i) == 0) {
        return i;
      }
    }
  }

  void print_stats() const {
    std::cout << "Stat " << print_prefix_
              << ": # TMs simulated = " << num_tms_total_ << std::endl;
    std::cout << "Stat " << print_prefix_
              << ": # TMs halted = " << num_tms_halt_ << std::endl;
  }

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm) {
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

    // TODO: Print progress.

    // Data needed for enumeration expansion.
    return {sim.is_halted(), sim.last_state(), sim.last_symbol()};
  }

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

void EnumerateAll(const int num_states, const int num_symbols, const long max_steps,
                  const std::string& out_witness_filename,
                  const std::string& out_nonhalt_filename) {
  Timer timer;
  std::cout << std::endl;
  std::cout << "Start: " << num_states << "x" << num_symbols << " : " << NowTimestamp() << std::endl;

  // Depth-first search of all TMs in TNF (but allowing A0->0R?).
  LazyBeaverEnum enumerator(max_steps, out_witness_filename, out_nonhalt_filename);
  enumerator.enumerate(new TuringMachine(num_states, num_symbols));
  const long lb = enumerator.min_missing();

  enumerator.print_stats();
  std::cout << "Stat : Runtime = " << timer.time_elapsed_s() << std::endl;

  // Print LB result
  std::cout << std::endl;
  if (lb < max_steps) {
    std::cout << "LB(" << num_states << ", " << num_symbols << ") = " << lb << std::endl;
  } else {
    std::cout << "Inconclusive: max_steps too small." << std::endl;
  }
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc < 5) {
    std::cerr << "Usage: lazy_beaver_enum num_states num_symbols max_steps out_witness_file [out_nonhalt_file]" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_witness_filename(argv[4]);
    std::string out_nonhalt_filename;
    if (argc >= 6) {
      out_nonhalt_filename.assign(argv[5]);
    }

    busy_beaver::EnumerateAll(num_states, num_symbols, max_steps,
                              out_witness_filename, out_nonhalt_filename);
  }
}
