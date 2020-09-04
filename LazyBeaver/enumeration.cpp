#include "enumeration.h"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <memory>
#include <set>
#include <stack>
#include <string>
#include <vector>

#include <ctime>

#include "turing_machine.h"


namespace lazy_beaver {
namespace {

void ExpandTM(const TuringMachine& tm,
              State last_state, Symbol last_symbol,
              std::stack<TuringMachine*>* todos) {
  int order = 0;

  for (State next_state = 0; next_state <= tm.max_next_state(); ++next_state) {
    for (Symbol next_symbol = 0; next_symbol <= tm.max_next_symbol(); ++next_symbol) {
      for (int next_move : {+1, -1}) {
        if (next_move == +1 || tm.next_move_left_ok()) {
          const TuringMachine::LookupResult next = {next_symbol, next_move, next_state};
          todos->push(new TuringMachine(tm, last_state, last_symbol, next, order));
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

}  // namespace


long Enumerate(int num_states, int num_symbols, long max_steps,
               std::ostream* outstream) {
  const auto start_time = std::chrono::system_clock::now();
  const std::time_t start_time_t = std::chrono::system_clock::to_time_t(start_time);

  std::cout << std::endl;
  std::cout << "Start: " << num_states << "x" << num_symbols << " : " << std::ctime(&start_time_t) << std::endl;

  // Depth-first search of all TMs in TNF (but allowing A0->0RB).
  // Note: These TMs will be deleted by the unique_ptr in the while loop below.
  std::stack<TuringMachine*> todos;
  // Start with empty TM.
  todos.push(new TuringMachine(num_states, num_symbols));
  std::set<long> steps_run;

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;

  while (todos.size() > 0) {
    std::unique_ptr<TuringMachine> tm(todos.top());
    todos.pop();
    auto result = DirectSimulate(*tm, max_steps);
    num_tms += 1;

    if (result.type == kHalt) {
      steps_run.insert(result.num_steps);
      if (tm->num_halts() > 1) {
        ExpandTM(*tm, result.last_state, result.last_symbol, &todos);
      }
      num_tms_halt += 1;
    } else if (outstream != nullptr) {
      WriteTuringMachine(*tm, outstream);
    }

    if (num_tms % 10000000 == 0) {
      std::cout << "Progress: TMs simulated: " << num_tms
                << " Provisional LB: " << MinMissing(steps_run)
                << " Current TM hereditary_order: " << tm->hereditary_name()
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


void ContinueEnumerateFromFile(std::istream* instream) {
  // TODO
}

}  // namespace lazy_beaver
