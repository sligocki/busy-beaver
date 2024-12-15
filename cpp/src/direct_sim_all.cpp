// Run DirectSimulator for all TMs in a file.

#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#include "simulator.h"
#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void DirectSimMain(const std::string& in_tms_filename, const long num_steps,
                   const std::string& out_tms_filename) {
  int num_total = 0;
  int num_halted = 0;
  int num_unknown = 0;
  // Go through all TMs in infile simulating each.
  std::ifstream in_tms_stream(in_tms_filename, std::ios::in | std::ios::binary);
  std::ofstream out_tms_stream(out_tms_filename, std::ios::out | std::ios::binary);

  // Standard Halting transition that we add to all halting TMs.
  const TuringMachine::LookupResult halt_trans = {
    1 /* next_symbol */, RIGHT, HaltState};

  while (true) {
    std::unique_ptr<TuringMachine> tm(ReadTuringMachineStream(&in_tms_stream, ""));
    if (tm == nullptr) {
      break;
    } else {
      DirectSimulator sim(*tm);
      sim.Seek(num_steps);
      num_total += 1;

      if (sim.is_halted()) {
        // Add halting transition if the TM halted.
        tm.reset(new TuringMachine(*tm, sim.last_state(), sim.last_symbol(), halt_trans, 0));
      }
      // Write results
      WriteTuringMachine(*tm, &out_tms_stream);
      if (sim.is_halted()) {
        num_halted += 1;
        out_tms_stream << " Halt " << sim.step_num() << " " << sim.tape().sigma_score() << std::endl;
      } else {
        num_unknown += 1;
        out_tms_stream << " Unknown " << sim.step_num() << std::endl;
      }
    }
  }

  std::cout << "Finished simulating " << num_steps << " steps"
            << "  Total: " << num_total
            << "  Halt: " << num_halted
            << "  Unknown: " << num_unknown
            << std::endl;
}

}  // namespace busy_beaver


int main(int argc, char* argv[]) {
  if (argc != 4) {
    std::cerr << "Usage: direct_sim_all in_tm_file num_steps out_tm_filename" << std::endl;
    return 1;
  } else {
    const std::string in_tms_filename(argv[1]);
    const long num_steps = std::stol(argv[2]);
    const std::string out_tms_filename(argv[3]);

    busy_beaver::DirectSimMain(in_tms_filename, num_steps, out_tms_filename);

    return 0;
  }
}
