#include "enumerator.h"

#include <memory>
#include <stack>

#include "turing_machine.h"
#include "util.h"


namespace busy_beaver {

void BaseEnumerator::enumerate(TuringMachine* init_tm) {
 std::stack<TuringMachine*> todos;
 todos.push(init_tm);

 while (!todos.empty()) {
   std::unique_ptr<TuringMachine> tm(todos.top());
   todos.pop();
   EnumExpandParams result = filter_tm(*tm);
   if (result.reached_undecided) {
     expand_tm(*tm, result, &todos);
   }

   // TODO: Write results?
   // TODO: Print progress?
 }
}

void BaseEnumerator::expand_tm(
    const TuringMachine& tm, const EnumExpandParams& result,
    std::stack<TuringMachine*>* todos) {
  // Don't expand the last remaining undecided cell (unless we are allowing
  // TMs with no halt transitions).
  if (allow_no_halt_ || tm.num_halts() > 1) {
    int order = 0;
    for (State next_state = 0; next_state <= tm.max_next_state(); ++next_state) {
      for (Symbol next_symbol = 0; next_symbol <= tm.max_next_symbol(); ++next_symbol) {
        for (int next_move : {+1, -1}) {
          if (next_move == +1 || tm.next_move_left_ok()) {
            const TuringMachine::LookupResult next = {next_symbol, next_move, next_state};
            todos->push(new TuringMachine(tm, result.last_state, result.last_symbol,
                                          next, order));
            order += 1;
          }
        }
      }
    }
  }
}

}  // namespace busy_beaver
