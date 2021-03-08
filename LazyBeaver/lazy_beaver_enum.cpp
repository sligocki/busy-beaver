// Prototype script for quickly calculating Lazy Beaver by enumerating
// candidates and directly simulating them on an uncompressed tape.

#include <fstream>
#include <iostream>
#include <map>
#include <stack>
#include <string>
#include <chrono>
#include <memory>

// #include <mpi.h>

#include "enumeration.h"
#include "turing_machine.h"


namespace lazy_beaver {

// Optimization parameters
// TODO(shawn or terry): These probably need to increase 5x2 case is spending
// 96% of time in communication.
#define MIN_NUM_JOBS_PER_BATCH 10
#define MAX_NUM_JOBS_PER_BATCH 25

#define DEFAULT_MAX_LOCAL_JOBS    30
#define DEFAULT_TARGET_LOCAL_JOBS 25

class WorkerWorkQueue {
  public:
    WorkerWorkQueue(int master_proc_num) {
      master_proc_num_ = master_proc_num;

      max_queue_size_    = DEFAULT_MAX_LOCAL_JOBS;
      target_queue_size_ = DEFAULT_TARGET_LOCAL_JOBS;
    }

    ~WorkerWorkQueue() {
    }

    TuringMachine *pop() {
      TuringMachine* tm = NULL;

      if (!local_queue_.empty()) {
        tm = local_queue_.top();
        local_queue_.pop();
      } else {
      }

      return tm;
    }

  private:
    int master_proc_num_;

    std::stack<TuringMachine*> local_queue_;

    int max_queue_size_;
    int target_queue_size_;
};


/*
class MasterWorkQueue {
  public:

};
*/

void EnumerateAll(int num_states, int num_symbols, long max_steps,
                  std::ofstream* out_steps_example_stream,
                  std::ofstream* out_nonhalt_stream) {
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
  Enumerate(&todos, max_steps, &steps_run, out_steps_example_stream, out_nonhalt_stream);

  long lb = MinMissing(steps_run);
  if (lb < max_steps) {
    std::cout << "LB(" << num_states << "," << num_symbols << ") = " << lb << std::endl;
  } else {
    std::cout << "Inconclusive: max_steps too small." << std::endl;
  }
}

}  // namespace lazy_beaver


int main(int argc, char* argv[]) {
  if (argc < 5) {
    std::cerr << "Usage: lazy_beaver_enum num_states num_symbols max_steps out_steps_example_file [out_nonhalt_file]" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    std::ofstream out_steps_example_stream(argv[4], std::ios::out | std::ios::binary);

    std::unique_ptr<std::ofstream> out_nonhalt_stream;
    if (argc >= 6) {
      // Write all non-halting machines to a file.
      std::ofstream out_nonhalt_stream(argv[5], std::ios::out | std::ios::binary);
      lazy_beaver::EnumerateAll(num_states, num_symbols, max_steps,
                                &out_steps_example_stream, &out_nonhalt_stream);
      out_nonhalt_stream.close();
    } else {
      // Don't write all non-halting machines to a file.
      lazy_beaver::EnumerateAll(num_states, num_symbols, max_steps,
                                &out_steps_example_stream, nullptr);
    }

    out_steps_example_stream.close();
  }
}
