#include "simulator.h"

#include <iostream>
#include <vector>

#include "turing_machine.h"


namespace busy_beaver {

Tape::Tape()
  : unit_size_(100),  // TODO: Optimize
    tape_(unit_size_, BlankSymbol),
    index_start_(tape_.size() / 2),  // Start in middle of tape.
    index_(index_start_) {}

Symbol Tape::read(const long pos) const {
  long index = pos + index_start_;
  if (0 <= index && index < tape_.size()) {
    return tape_[index];
  } else {
    return BlankSymbol;
  }
}

void Tape::move(const long move_dir) {
  index_ += move_dir;
  // Extend tape if necessary.
  if (index_ < 0) {
    tape_.insert(tape_.begin(), unit_size_, BlankSymbol);
    index_ += unit_size_;
    index_start_ += unit_size_;
  } else if (index_ >= tape_.size()) {
    tape_.insert(tape_.end(), unit_size_, BlankSymbol);
  }
}

void Tape::print() const {
  std::cout << -index_start_ << " to " << tape_.size() << " ";
  for (const Symbol element : tape_) {
    std::cout << element;
  }
  std::cout << std::endl;
}

DirectSimulator::DirectSimulator(const TuringMachine& tm)
  : tm_(tm),
    state_(InitialState),
    step_num_(0) {}

void DirectSimulator::StepSafe() {
  // Step w/o checking halt status. Only for internal use.
  last_state_ = state_;
  last_symbol_ = tape_.read();
  auto lookup_res = tm_.Lookup(last_state_, last_symbol_);

  tape_.write(lookup_res.symbol);
  tape_.move(lookup_res.move);
  state_ = lookup_res.state;
  step_num_ += 1;
}

void DirectSimulator::Step() {
  if (!is_halted()) {
    StepSafe();
  }
}

void DirectSimulator::Seek(const long step_goal) {
  while (!is_halted() && step_num_ < step_goal) {
    StepSafe();
  }
}

}  // namespace busy_beaver
