#ifndef BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
#define BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_

#include <iostream>
#include <map>
#include <stack>

#include "turing_machine.h"


namespace lazy_beaver {

// Enumerates TMs in TNF starting from tms (up to max_steps).
// Prints a bunch of info.
// Writes:
//  * Example TM for every unique num_steps found to out_steps_example_stream.
//  * Not yet halting machines to out_nonhalt_stream (if non-NULL)
// This function modifies tms stack.
void Enumerate(std::stack<TuringMachine*>* tms,
               long max_steps,
               std::set<long>* steps_run,
               std::ostream* out_steps_example_stream,
               std::ostream* out_nonhalt_stream = nullptr);

// Finds minimum positive integer which is not a key to collection.
// Useful for calculating Lazy Beaver.
long MinMissing(const std::set<long>& collection);

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
