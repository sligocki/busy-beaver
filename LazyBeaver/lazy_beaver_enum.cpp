// Prototype script for quickly calculating Lazy Beaver by enumerating
// candidates and directly simulating them on an uncomressed tape.

#include <algorithm>
#include <chrono>
#include <iostream>
#include <set>
#include <stack>
#include <string>
#include <vector>

#include <ctime>


namespace lazy_beaver {

using Symbol = int;
using State = int;
const Symbol EmptySymbol = 0;
const State InitialState = 0;
const State HaltState = -1;

class TuringMachine {
 public:
  struct LookupResult {
    Symbol symbol;
    int move;  // +1 for Right, -1 for Left.
    State state;
  };

  LookupResult Lookup(State state, Symbol symbol) const {
    return transitions_[state][symbol];
  }


  State max_next_state() const { return max_next_state_; }
  Symbol max_next_symbol() const { return max_next_symbol_; }
  bool next_move_left_ok() const { return next_move_left_ok_; }
  int num_halts() const { return num_halts_; }
  const std::string& hereditary_name() const { return hereditary_name_; }

  // Empty TM
  TuringMachine(int num_states, int num_symbols)
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
  TuringMachine(const TuringMachine& old_tm,
                const State& last_state, const Symbol& last_symbol,
                const LookupResult& next_trans,
                int hereditary_sub_order)
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

 private:
  int num_states_;
  int num_symbols_;
  State max_next_state_;
  Symbol max_next_symbol_;
  bool next_move_left_ok_;
  int num_halts_;
  std::string hereditary_name_;
  std::vector<std::vector<LookupResult>> transitions_;
};


enum ResultType {
  kHalt,
  kMaxSteps
};

struct SimResult {
  ResultType type;
  long num_steps;
  State last_state;
  Symbol last_symbol;
};

// Directly simulate at Turing Machine on a finite tape without tape compression.
SimResult DirectSimulate(
    const TuringMachine& tm, const long max_steps) {
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


void ExpandTM(const TuringMachine& tm,
              State last_state, Symbol last_symbol,
              std::stack<TuringMachine>* todos) {
  int order = 0;
  for (State next_state = 0; next_state <= tm.max_next_state(); ++next_state) {
    for (Symbol next_symbol = 0; next_symbol <= tm.max_next_symbol(); ++next_symbol) {
      for (int next_move : {+1, -1}) {
        if (next_move == +1 || tm.next_move_left_ok()) {
          const TuringMachine::LookupResult next = {next_symbol, next_move, next_state};
          todos->emplace(tm, last_state, last_symbol, next, order);
          order += 1;
        }
      }
    }
  }
}

long MinMissing(const std::set<long> collection) {
  for (long i = 1;; ++i) {
    if (collection.count(i) == 0) {
      return i;
    }
  }
}

double TimeSince(std::chrono::time_point<std::chrono::system_clock> start_time) {
  const auto end_time = std::chrono::system_clock::now();
  std::chrono::duration<double> diff = end_time - start_time;
  return diff.count();
}

long Enumerate(int num_states, int num_symbols, long max_steps) {
  const auto start_time = std::chrono::system_clock::now();
  const std::time_t start_time_t = std::chrono::system_clock::to_time_t(start_time);
  std::cout << std::endl;
  std::cout << "Start: " << num_states << "x" << num_symbols << " : " << std::ctime(&start_time_t);

  // Depth-first search of all TMs in TNF (but allowing A0->0RB).
  std::stack<TuringMachine> todos;
  TuringMachine empty_tm(num_states, num_symbols);
  todos.push(empty_tm);
  std::set<long> steps_run;

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;

  while (todos.size() > 0) {
    TuringMachine tm = todos.top();
    todos.pop();
    auto result = DirectSimulate(tm, max_steps);
    num_tms += 1;

    if (result.type == kHalt) {
      steps_run.insert(result.num_steps);
      if (tm.num_halts() > 1) {
        ExpandTM(tm, result.last_state, result.last_symbol, &todos);
      }
      num_tms_halt += 1;
    }
    if (num_tms % 10000000 == 0) {
      std::cout << "Progress: TMs simulated: " << num_tms
                << " Provisional LB: " << MinMissing(steps_run)
                << " Current TM hereditary_order: " << tm.hereditary_name()
                << " Stack size: " << todos.size()
                << " Runtime: " << TimeSince(start_time)
                << std::endl;
    }
  }

  std::cout << "Stat: # TMs simulated = " << num_tms << std::endl;
  std::cout << "Stat: # TMs halted = " << num_tms_halt << std::endl;
  std::cout << "Stat: Runtime = " << TimeSince(start_time) << std::endl;

  long lb = MinMissing(steps_run);
  if (lb < max_steps) {
    std::cout << "LB(" << num_states << "," << num_symbols << ") = " << lb << std::endl;
    return lb;
  }

  std::cout << "Inconclusive: max_steps too small." << std::endl;
  return -1;
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: lazy_beaver_enum num_states num_symbols max_steps" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);

    if (lazy_beaver::Enumerate(num_states, num_symbols, max_steps) < 0) {
      // Error/inconclusive
      return 1;
    } else {
      // Success
      return 0;
    }
  }
}
