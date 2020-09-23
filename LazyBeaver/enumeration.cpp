#include "enumeration.h"

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <map>
#include <memory>
#include <queue>
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


long MinMissing(const std::set<long>& collection) {
  for (long i = 1;; ++i) {
    if (collection.count(i) == 0) {
      return i;
    }
  }
}

struct BBBCandidate {
  TuringMachine* tm;
  State beep_state;
  long beep_last_step;

  // Comparison Functor
  // Note: Greater than testing so that the top() element in the queue will be the smallest.
  bool operator()(const BBBCandidate &a, const BBBCandidate &b) {
    return a.beep_last_step > b.beep_last_step;
  };
};

// Simple efficient class for keeping the max k elements added into it.
class TopK {
 public:
  TopK(long k) : max_size_(k) {}

  // Is this enough steps to make it into the TopK?
  bool IsInTop(long steps) const {
    if (queue_.size() < max_size_) {
      // Queue isn't full yet, we accept anything.
      return true;
    } else if (steps > queue_.top().beep_last_step) {
      // Queue is full, but this is better than the worst element we have.
      return true;
    } else {
      // Queue is full and this is worse than the worse element we have, reject.
      return false;
    }
  }

  // Takes ownership of val.tm
  void Insert(const BBBCandidate& val) {
    // Note: This is inefficient if !IsInTop(val.beep_last_step)
    queue_.push(val);
    // If we've collected too many things, remove the smallest.
    if (queue_.size() > max_size_) {
      Pop();
    }
  }

  bool Empty() const { return queue_.empty(); }
  const BBBCandidate& Top() const { return queue_.top(); }
  void Pop() {
    // Avoid memory leak.
    delete Top().tm;
    queue_.pop();
  }

 private:
  long max_size_ = 0;

  // queue_.top() is the smallest value we are tracking.
  std::priority_queue<BBBCandidate, std::vector<BBBCandidate>, BBBCandidate>
    queue_;
};

void Enumerate(std::stack<TuringMachine*>* todos,
               long max_steps,
               // TODO: long bbb_top_count,
               std::set<long>* steps_run,
               std::ostream* out_steps_example_stream,
               std::ostream* out_nonhalt_stream,
               std::ostream* save_stack_stream,
               int proc_num) {
  const auto start_time = std::chrono::system_clock::now();

  // Stats
  long num_tms = 0;
  long num_tms_halt = 0;
  // BBB: Track top k Beeping Busy Beaver candidates.
  long bbb_top_count = 10;
  TopK bbb_top(bbb_top_count);

  while (todos->size() > 0 &&
         (save_stack_stream == nullptr || !std::filesystem::exists("stop.enumeration"))) {
    std::unique_ptr<TuringMachine> tm(todos->top());
    todos->pop();
    auto result = DirectSimulate(*tm, max_steps);
    num_tms += 1;

    // std::cout << result.num_steps << "\t" << result.beep_state << "\t" << result.beep_last_step << "\t";
    // WriteTuringMachine(*tm, &std::cout);

    if (result.type == kHalt) {
      if (tm->num_halts() > 0) {  // TODO: BBB has to allow non-halting machines.
        ExpandTM(*tm, result.last_state, result.last_symbol, todos);
      }
      if (steps_run->count(result.num_steps) == 0) {
        steps_run->insert(result.num_steps);
        // We found a new run-length, write it to steps_example file.
        *out_steps_example_stream << result.num_steps << "\t";
        WriteTuringMachine(*tm, out_steps_example_stream);
        out_steps_example_stream->flush();
      }
      num_tms_halt += 1;
    } else {
      // Non-halting machine.
      if (out_nonhalt_stream != nullptr) {
        WriteTuringMachine(*tm, out_nonhalt_stream);
      }
    }

    if (result.beep_last_step != -1 && bbb_top.IsInTop(result.beep_last_step)) {
      // If this is a BBB candidate
      const BBBCandidate candidate{tm.release(), result.beep_state, result.beep_last_step};
      bbb_top.Insert(candidate);
    }

    if (num_tms % 10000000 == 0) {
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
  }

  // TODO: process bbb_top.
  std::ostream* out_bbb_stream = &std::cout;
  while (!bbb_top.Empty()) {
    const BBBCandidate& candidate = bbb_top.Top();
    *out_bbb_stream << "Proc: " << proc_num << "\t"
      << candidate.beep_last_step << "\t"
      << candidate.beep_state << "\t";
    WriteTuringMachine(*candidate.tm, out_bbb_stream);
    bbb_top.Pop();
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
