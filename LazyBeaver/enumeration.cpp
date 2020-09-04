#include "enumeration.h"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <map>
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

double TimeSince(std::chrono::time_point<std::chrono::system_clock> start_time) {
  const auto end_time = std::chrono::system_clock::now();
  std::chrono::duration<double> diff = end_time - start_time;
  return diff.count();
}

}  // namespace


long MinMissing(const std::map<long, TuringMachine*>& collection) {
  for (long i = 1;; ++i) {
    if (collection.count(i) == 0) {
      return i;
    }
  }
}

void Enumerate(std::stack<TuringMachine*>* todos,
               long max_steps,
               std::map<long, TuringMachine*>* steps_example,
               std::ostream* out_nonhalt_stream) {
  const auto start_time = std::chrono::system_clock::now();

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;

  while (todos->size() > 0) {
    std::unique_ptr<TuringMachine> tm(todos->top());
    todos->pop();
    auto result = DirectSimulate(*tm, max_steps);
    num_tms += 1;

    if (num_tms % 10000000 == 0) {
      std::cout << "Progress: TMs simulated: " << num_tms
                << " Provisional LB: " << MinMissing(*steps_example)
                << " Current TM hereditary_order: " << tm->hereditary_name()
                << " Stack size: " << todos->size()
                << " Runtime: " << TimeSince(start_time)
                << std::endl;
    }

    if (result.type == kHalt) {
      if (tm->num_halts() > 1) {
        ExpandTM(*tm, result.last_state, result.last_symbol, todos);
      }

      if (steps_example->find(result.num_steps) == steps_example->end()) {
        (*steps_example)[result.num_steps] = tm.release();
        // NOTE: Do not use tm after this point!
      }
      num_tms_halt += 1;
    } else if (out_nonhalt_stream != nullptr) {
      WriteTuringMachine(*tm, out_nonhalt_stream);
    }
  }

  std::cout << "Stat: # TMs simulated = " << num_tms << std::endl;
  std::cout << "Stat: # TMs halted = " << num_tms_halt << std::endl;
  std::cout << "Stat: Runtime = " << TimeSince(start_time) << std::endl;
}

}  // namespace lazy_beaver
