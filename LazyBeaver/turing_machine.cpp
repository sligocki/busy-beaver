#include "turing_machine.h"


namespace lazy_beaver {

// Empty TM
TuringMachine::TuringMachine(int num_states, int num_symbols)
    : num_states_(num_states), num_symbols_(num_symbols),
      max_next_state_(1), max_next_symbol_(1),
      next_move_left_ok_(false), num_halts_(num_states * num_symbols),
      hereditary_name_() {
  const LookupResult empty_trans = {1, +1, HaltState};
  for (int i = 0; i < num_states; ++i) {
    transitions_.emplace_back(num_symbols, empty_trans);
  }
}

// TM built from a previous TM
TuringMachine::TuringMachine(
  const TuringMachine& old_tm,
  const State& last_state, const Symbol& last_symbol,
  const LookupResult& next_trans, int hereditary_sub_order)
    : num_states_(old_tm.num_states_), num_symbols_(old_tm.num_symbols_),
      next_move_left_ok_(true), num_halts_(old_tm.num_halts_ - 1) {
  max_next_state_ = std::max(old_tm.max_next_state_,
                             std::min(num_states_ - 1, next_trans.state + 1));
  max_next_symbol_ = std::max(old_tm.max_next_symbol_,
                             std::min(num_symbols_ - 1, next_trans.symbol + 1));
  hereditary_name_ = old_tm.hereditary_name_;
  hereditary_name_.append(",");
  hereditary_name_.append(std::to_string(hereditary_sub_order));
  // Initialize ttable to old_tm's ttable.
  transitions_.resize(num_states_);
  for (State state = 0; state < num_states_; ++state) {
    transitions_[state].resize(num_symbols_);
    for (Symbol symbol = 0; symbol < num_symbols_; ++symbol) {
      transitions_[state][symbol] = old_tm.transitions_[state][symbol];
    }
  }
  // Update one trans.
  transitions_[last_state][last_symbol] = next_trans;
}


SimResult DirectSimulate(const TuringMachine& tm, const long max_steps) {
  const int unit_size = 10;
  std::vector<Symbol> tape(unit_size, EmptySymbol);
  long pos = tape.size() / 2;
  State state = InitialState;

  long num_steps = 0;

  while (true) {
    State in_state = state;
    Symbol in_symbol = tape[pos];
    auto lookup_res = tm.Lookup(in_state, in_symbol);
    tape[pos] = lookup_res.symbol;
    pos += lookup_res.move;
    state = lookup_res.state;
    num_steps += 1;

    if (state == HaltState) {
      return {kHalt, num_steps, in_state, in_symbol};
    }

    if (num_steps >= max_steps) {
      return {kMaxSteps, num_steps, in_state, in_symbol};
    }

    // Extend tape if necessary.
    if (pos < 0) {
      tape.insert(tape.begin(), unit_size, EmptySymbol);
      pos += unit_size;
    } else if (pos >= tape.size()) {
      tape.insert(tape.end(), unit_size, EmptySymbol);
    }
  }
}

}  // namespace lazy_beaver
