#include "turing_machine.h"

#include <iostream>
#include <string>


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

// TM from transition table.
TuringMachine::TuringMachine(
  const std::vector<std::vector<LookupResult>>& transitions,
  const std::string& base_name)
    : hereditary_name_(base_name), transitions_(transitions) {
  // Calculate details about TTable.
  State max_state = 0;
  Symbol max_symbol = 0;
  int num_halts = 0;
  for (const auto& row : transitions_) {
    for (const LookupResult& trans : row) {
      max_state = std::max(max_state, trans.state);
      max_symbol = std::max(max_symbol, trans.symbol);
      if (trans.state < 0) {
        num_halts += 1;
      }
    }
  }

  num_states_ = transitions_.size();
  num_symbols_ = transitions_[0].size();
  max_next_state_ = std::min(max_state + 1, num_states_ - 1);
  max_next_symbol_ = std::min(max_symbol + 1, num_symbols_ - 1);
  // Assume we aren't starting with completely blank TM.
  next_move_left_ok_ = true;
  num_halts_ = num_halts;
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


#define ASSERT(expr) \
  if (!(expr)) { \
    std::cerr << "ASSERT: " #expr " failed @ " << __FILE__ << ":" << __LINE__ << std::endl; \
    exit(1); \
  }

void WriteTuringMachine(const TuringMachine& tm, std::ostream* outstream) {
  ASSERT(tm.num_states() < 26);
  ASSERT(tm.num_symbols() < 10);
  for (State in_state = 0; in_state < tm.num_states(); ++in_state) {
    for (Symbol in_symbol = 0; in_symbol < tm.num_symbols(); ++in_symbol) {
      auto trans = tm.Lookup(in_state, in_symbol);
      // Output format: 1RB (write symbol, move dir, next state).
      *outstream << trans.symbol;
      if (trans.move == +1) {
        *outstream << "R";
      } else {
        ASSERT(trans.move == -1);
        *outstream << "L";
      }
      char out_state_char;
      if (trans.state >= 0) {
        // 0 -> 'A', 1 -> 'B', ...
        out_state_char = trans.state + 'A';
      } else {
        out_state_char = 'Z';
      }
      *outstream << out_state_char;
      // Space separate each cell in a row.
      *outstream << " ";
    }
    // Double space separate each row in the transition table.
    *outstream << " ";
  }
  // Each TM goes on it's own newline.
  *outstream << "\n";
}

TuringMachine* ReadTuringMachine(std::istream* instream) {
  std::string line;
  if (std::getline(*instream, line)) {
    int i = 0;
    std::vector<std::vector<TuringMachine::LookupResult>> transitions;
    while (i < line.size()) {
      std::vector<TuringMachine::LookupResult> row;
      // Each trans in a row takes up exactly 4 bytes, Ex: "1RB ".
      // End of row is indicated by a double space ("  ").
      for (;line[i] != ' '; i += 4) {
        TuringMachine::LookupResult trans;
        // Format: 1RB (write symbol, move dir, next state).
        // '0' -> 0, '1' -> 1, ...
        trans.symbol = line[i] - '0';
        ASSERT(0 <= trans.symbol && trans.symbol <= 9);
        if (line[i+1] == 'R') {
          trans.move = +1;
        } else {
          ASSERT(line[i+1] == 'L');
          trans.move = -1;
        }
        char state_char = line[i+2];
        if (state_char == 'Z') {
          trans.state = -1;
        } else {
          // 'A' -> 0, 'B' -> 1, ...
          trans.state = state_char - 'A';
          ASSERT(0 <= trans.state && trans.state < 26);
        }
        ASSERT(line[i+3] == ' ');
        row.push_back(trans);
      }
      // We've reached "  " which indicates the end of a row.
      transitions.push_back(row);
      i += 1;
    }
    const std::string base_name = "TODO";
    return new TuringMachine(transitions, base_name);

  } else {
    // Couldn't read line, so we're done.
    return nullptr;
  }
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
