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
#include <experimental/filesystem>

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


long MinMissing(const std::set<long>& collection) {
  for (long i = 1;; ++i) {
    if (collection.count(i) == 0) {
      return i;
    }
  }
}

void Enumerate(std::stack<TuringMachine*>* todos,
               long max_steps,
               std::set<long>* steps_run,
               std::ostream* out_steps_example_stream,
               std::ostream* out_nonhalt_stream,
               std::ostream* save_stack_stream,
               int proc_num,
               std::string stop_name) {
  const auto start_time = std::chrono::system_clock::now();
  auto check_time = start_time;

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;

  // while (todos->size() > 0 &&
  //        (save_stack_stream == nullptr || !std::experimental::filesystem::exists("stop.enumeration"))) {
  while (todos->size() > 0) {
    std::unique_ptr<TuringMachine> tm(todos->top());
    todos->pop();
    auto result = DirectSimulate(*tm, max_steps);
    num_tms += 1;

    if ((num_tms == 1) || ((num_tms % 10000000) == 0)) {
      if (proc_num >= 0) {
        std::cout << "Progress " << proc_num << ":";
      } else {
        std::cout << "Progress:";
      }

      std::cout << " TMs simulated: " << num_tms
                << " Provisional LB: " << MinMissing(*steps_run)
                << " Current TM hereditary_order: " << tm->hereditary_name()
                << " Stack size: " << todos->size()
                << " Runtime: " << TimeSince(start_time)
                << std::endl;
    }

    if (result.type == kHalt) {
      if (tm->num_halts() > 1) {
        ExpandTM(*tm, result.last_state, result.last_symbol, todos);
      }
      if (steps_run->count(result.num_steps) == 0) {
        steps_run->insert(result.num_steps);
        // We found a new run-length, write it to steps_example file.
        if (out_steps_example_stream != nullptr) {
          *out_steps_example_stream << result.num_steps << "\t";
          WriteTuringMachine(*tm, out_steps_example_stream);
          // out_steps_example_stream->flush();
        }
      }
      num_tms_halt += 1;
    } else {
      // Non-halting machine.
      if (out_nonhalt_stream != nullptr) {
        WriteTuringMachine(*tm, out_nonhalt_stream);
      }
    }

    if (save_stack_stream != nullptr) {
      if (TimeSince(check_time) >= 10.0) {
        if (std::experimental::filesystem::exists(stop_name.c_str())) {
          break;
        }

        check_time = std::chrono::system_clock::now();
      }
    }
  }

  if (proc_num >= 0) {
    std::cout << "Stat " << proc_num << ": # TMs simulated = " << num_tms << std::endl;
    std::cout << "Stat " << proc_num << ": # TMs halted = " << num_tms_halt << std::endl;
    std::cout << "Stat " << proc_num << ": Runtime = " << TimeSince(start_time) << std::endl;
  } else {
    std::cout << "Stat: # TMs simulated = " << num_tms << std::endl;
    std::cout << "Stat: # TMs halted = " << num_tms_halt << std::endl;
    std::cout << "Stat: Runtime = " << TimeSince(start_time) << std::endl;
  }

  if (save_stack_stream != nullptr) {
    while (todos->size() > 0) {
      std::unique_ptr<TuringMachine> tm(todos->top());
      todos->pop();
      WriteTuringMachine(*tm, save_stack_stream);
    }
  }
}

}  // namespace lazy_beaver
