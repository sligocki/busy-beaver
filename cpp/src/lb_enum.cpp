// Prototype script for quickly calculating Lazy Beaver by enumerating
// candidates and directly simulating them on an uncompressed tape.

#include <fstream>
#include <iostream>
#include <string>

#include "lazy_beaver_enumerator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void EnumerateAll(const int num_states, const int num_symbols, const long max_steps,
                  const std::string& out_witness_filename,
                  const std::string& out_nonhalt_filename) {
  Timer timer;
  std::cout << std::endl;
  std::cout << "Start: " << num_states << "x" << num_symbols << " : " << NowTimestamp() << std::endl;

  // Depth-first search of all TMs in TNF (but allowing A0->0R?).
  LazyBeaverEnum enumerator(max_steps, out_witness_filename, out_nonhalt_filename);
  enumerator.enumerate(new TuringMachine(num_states, num_symbols));

  enumerator.print_stats();
  std::cout << "Stat : Runtime = " << timer.time_elapsed_s() << std::endl;

  // Print LB result
  std::cout << std::endl;
  const long lb = enumerator.min_missing();
  if (lb < max_steps) {
    std::cout << "LB(" << num_states << ", " << num_symbols << ") = " << lb << std::endl;
  } else {
    std::cout << "Inconclusive: max_steps too small." << std::endl;
  }
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc < 5) {
    std::cerr << "Usage: lazy_beaver_enum num_states num_symbols max_steps out_witness_file [out_nonhalt_file]" << std::endl;
    return 1;
  } else {
    const int num_states = std::stoi(argv[1]);
    const int num_symbols = std::stoi(argv[2]);
    const long max_steps = std::stol(argv[3]);
    const std::string out_witness_filename(argv[4]);
    std::string out_nonhalt_filename;
    if (argc >= 6) {
      out_nonhalt_filename.assign(argv[5]);
    }

    busy_beaver::EnumerateAll(num_states, num_symbols, max_steps,
                              out_witness_filename, out_nonhalt_filename);
  }
}
