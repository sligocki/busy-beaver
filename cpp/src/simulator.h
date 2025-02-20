#ifndef BUSY_BEAVER_SIMULATOR_H_
#define BUSY_BEAVER_SIMULATOR_H_

#include <vector>

#include "turing_machine.h"


namespace busy_beaver {

class Tape {
 public:
  Tape();

  Symbol read() const { return tape_[index_]; }
  Symbol read(long pos) const;
  void write(const Symbol symb);
  void move(const long move_dir);

  // Position on tape (relative to start position.)
  long position() const { return index_ - index_start_; }
  bool in_range(const long pos) const {
    long index = pos + index_start_;
    return (0 <= index && index < tape_.size());
  }

  void print() const;

  // Evaluate various Busy Beaver functions on the tape.
  // Rado Sigma score (number of non-zero symbols on tape).
  long sigma_score() const;
  // Ben-Amram space (number of TM cells read).
  //   Note: We actually count number or cells _written_, but these are the same
  //   for this TM definition.
  //   Note: This may not be the same as the number of cells _visited_ since it
  //   does not (necessarily) count the final head position (which is never read).
  long space() const { return max_index_ - min_index_ + 1; }

 private:
  const long unit_size_;
  std::vector<Symbol> tape_;
  long index_start_;
  long index_;
  // Track subset of tape written to (in order to compute BB_space).
  long min_index_;
  long max_index_;
};

class DirectSimulator {
 public:
  DirectSimulator(const TuringMachine& tm);

  void Step();
  void Seek(const long step_goal);

  bool is_halted() const { return state_ == HaltState; }

  const Tape& tape() const { return tape_; }
  State state() const { return state_; }
  long step_num() const { return step_num_; }
  State last_state() const { return last_state_; }
  Symbol last_symbol() const { return last_symbol_; }

 private:
  void StepSafe();

  const TuringMachine& tm_;
  Tape tape_;
  State state_;
  long step_num_;
  // Last state in and symbol read before halting.
  State last_state_;
  Symbol last_symbol_;
};

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_SIMULATOR_H_
