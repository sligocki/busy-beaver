#ifndef BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
#define BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_

#include <iostream>
#include <stack>

#include "turing_machine.h"


namespace lazy_beaver {

// Enumerate TMs in TNF starting from tms (up to max_steps).
// Print a bunch of info.
// If outstream is non-NULL, write out all the not (yet) halted machines to it.
// This function will modify tms stack.
//
// TODO: Return map of TMs by runtime.
void Enumerate(std::stack<TuringMachine*>* tms,
               long max_steps,
               std::ostream* outstream = nullptr);

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
