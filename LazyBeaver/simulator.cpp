#include "simulator.h"

#include <vector>

#include "turing_machine.h"


namespace lazy_beaver {

DirectSimulator::DirectSimulator(const TuringMachine& tm)
  : tm_(tm),
    unit_size_(100000),  // TODO: Optimize
    tape_(unit_size_, EmptySymbol),
    index_start_(tape_.size() / 2),  // Start in middle of tape.
    index_(index_start_),
    state_(InitialState),
    step_num_(0) {}

void DirectSimulator::Step() {
  last_state_ = state_;
  last_symbol_ = tape_[index_];
  auto lookup_res = tm_.Lookup(last_state_, last_symbol_);
  // Write
  tape_[index_] = lookup_res.symbol;
  // Move
  index_ += lookup_res.move;
  // Change state
  state_ = lookup_res.state;
  step_num_ += 1;

  // Extend tape if necessary.
  if (index_ < 0) {
    tape_.insert(tape_.begin(), unit_size_, EmptySymbol);
    index_ += unit_size_;
    index_start_ += unit_size_;
  } else if (index_ >= tape_.size()) {
    tape_.insert(tape_.end(), unit_size_, EmptySymbol);
  }
}

void DirectSimulator::Seek(const long step_goal) {
  while (!is_halted() && step_num_ < step_goal) {
    Step();
  }
}

}  // namespace lazy_beaver
