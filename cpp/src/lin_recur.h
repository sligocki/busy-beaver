#ifndef BUSY_BEAVER_LIN_RECUR_H_
#define BUSY_BEAVER_LIN_RECUR_H_

#include "turing_machine.h"


namespace busy_beaver {

struct LinRecurResult {
  bool is_halted;
  bool is_lin_recurrent;
  long lr_start_step;
  long lr_period;
  long lr_offset;
  State last_state;
  Symbol last_symbol;
  long max_ref_config_step;
  long steps_run;
  long sigma_score;
};

// Search for Lin Recurrence detectable within the first max_steps.
// Note: This will actually run until we reach the power of 2 larger than max_steps
// and can only detect LR cycles with period, start_step < the previous power of 2.
LinRecurResult LinRecurDetect(const TuringMachine& tm, const long max_steps);

// Verify a specific LR period and start_step.
LinRecurResult LinRecurCheck(const TuringMachine& tm,
                             const long start_step, const long period);

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_LIN_RECUR_H_
