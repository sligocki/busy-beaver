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
};

LinRecurResult LinRecurDetect(const TuringMachine& tm, const long max_steps);

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_LIN_RECUR_H_
