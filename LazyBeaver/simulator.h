#ifndef BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_
#define BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_

#include <vector>

#include "turing_machine.h"


namespace lazy_beaver {

class DirectSimulator {
 public:
  DirectSimulator(const TuringMachine& tm);

  void Step();
  void Seek(const long step_goal);

  bool is_halted() const { return state_ == HaltState; }
  // Position on tape (relative to start position.)
  long position() const { return index_ - index_start_; }

  State state() const { return state_; }
  long step_num() const { return step_num_; }
  State last_state() const { return last_state_; }
  Symbol last_symbol() const { return last_symbol_; }
  const std::vector<Symbol>& tape() const { return tape_; }

 private:
  const TuringMachine& tm_;
  const long unit_size_;
  std::vector<Symbol> tape_;
  long index_start_;
  long index_;
  State state_;
  long step_num_;
  // Last state in and symbol read before halting.
  State last_state_;
  Symbol last_symbol_;
};

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_
