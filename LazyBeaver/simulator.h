#ifndef BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_
#define BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_

#include <vector>

#include "turing_machine.h"


namespace lazy_beaver {

class Tape {
 public:
  Tape();

  Symbol read() const { return tape_[index_]; }
  Symbol read(long pos) const;
  void write(const Symbol symb) { tape_[index_] = symb; }
  void move(const long move_dir);

  // Position on tape (relative to start position.)
  long position() const { return index_ - index_start_; }
  bool in_range(const long pos) const {
    long index = pos + index_start_;
    return (0 <= index && index < tape_.size());
  }

  void print() const;

 private:
  const long unit_size_;
  std::vector<Symbol> tape_;
  long index_start_;
  long index_;
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
  const TuringMachine& tm_;
  Tape tape_;
  State state_;
  long step_num_;
  // Last state in and symbol read before halting.
  State last_state_;
  Symbol last_symbol_;
};

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_SIMULATOR_H_
