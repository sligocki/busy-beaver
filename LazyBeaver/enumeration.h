#ifndef BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
#define BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_

#include <iostream>
#include <map>
#include <stack>

#include "turing_machine.h"


namespace lazy_beaver {

// Enumerate TMs in TNF starting from tms (up to max_steps).
// Print a bunch of info.
// If outstream is non-NULL, write out all the not (yet) halted machines to it.
//
// Returns steps_example: a map: num_steps -> example TM that acheives this #.
//
// This function will modify tms stack.
void Enumerate(std::stack<TuringMachine*>* tms,
               long max_steps,
               std::map<long, TuringMachine*>* steps_example,
               std::ostream* out_nonhalt_stream = nullptr);

// Find minimum positive integer which is not a key to collection.
// Useful for calculating Lazy Beaver.
long MinMissing(const std::map<long, TuringMachine*>& collection);

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
