#include "enumeration.h"

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <stack>
#include <string>
#include <vector>

#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {


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
  Timer timer;
  Timer check_timer;

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;

  // while (todos->size() > 0 &&
  //        (save_stack_stream == nullptr || !std::filesystem::exists("stop.enumeration"))) {
  while (todos->size() > 0) {
    std::unique_ptr<TuringMachine> tm(todos->top());
    todos->pop();
    DirectSimulator sim(*tm);
    sim.Seek(max_steps);
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
                << " Runtime: " << timer.time_elapsed_s()
                << std::endl;
    }

    if (sim.is_halted()) {
      if (tm->num_halts() > 1) {
        ExpandTM(*tm, sim.last_state(), sim.last_symbol(), todos);
      }
      if (steps_run->count(sim.step_num()) == 0) {
        steps_run->insert(sim.step_num());
        // We found a new run-length, write it to steps_example file.
        if (out_steps_example_stream != nullptr) {
          *out_steps_example_stream << sim.step_num() << "\t";
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
      if (check_timer.time_elapsed_s() >= 10.0) {
        if (std::filesystem::exists(stop_name.c_str())) {
          break;
        }

        check_timer.restart_timer();
      }
    }
  }

  if (proc_num >= 0) {
    std::cout << "Stat " << proc_num << ": # TMs simulated = " << num_tms << std::endl;
    std::cout << "Stat " << proc_num << ": # TMs halted = " << num_tms_halt << std::endl;
    std::cout << "Stat " << proc_num << ": Runtime = " << timer.time_elapsed_s() << std::endl;
  } else {
    std::cout << "Stat: # TMs simulated = " << num_tms << std::endl;
    std::cout << "Stat: # TMs halted = " << num_tms_halt << std::endl;
    std::cout << "Stat: Runtime = " << timer.time_elapsed_s() << std::endl;
  }

  if (save_stack_stream != nullptr) {
    while (todos->size() > 0) {
      std::unique_ptr<TuringMachine> tm(todos->top());
      todos->pop();
      WriteTuringMachine(*tm, save_stack_stream);
    }
  }
}

}  // namespace busy_beaver
