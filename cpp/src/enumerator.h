#ifndef BUSY_BEAVER_ENUMERATOR_H_
#define BUSY_BEAVER_ENUMERATOR_H_

#include <stack>

#include "turing_machine.h"


namespace busy_beaver {

struct EnumExpandParams {
  bool reached_undecided;
  State last_state;
  Symbol last_symbol;
};

// Abstract base class. Concrete subclasses must implement filter_tm().
class BaseEnumerator {
 public:
  BaseEnumerator(bool allow_no_halt)
    : allow_no_halt_(allow_no_halt) {}
  virtual ~BaseEnumerator() {}

  // Enumerate all TMs children of `tm` running each through filter_tm().
  // Takes ownership of `tm`
  void enumerate(TuringMachine* tm);

 private:
  virtual EnumExpandParams filter_tm(const TuringMachine& tm) = 0;
  void expand_tm(const TuringMachine& tm, const EnumExpandParams& result,
                 std::stack<TuringMachine*>* todos);

  // Options
  const bool allow_no_halt_;
};

}  // namespace busy_beaver

#endif  // BUSY_BEAVER_ENUMERATOR_H_
