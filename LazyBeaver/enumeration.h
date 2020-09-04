#ifndef BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
#define BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_

#include <iostream>


namespace lazy_beaver {

// Enumerate all AxB TMs in TNF for up to max_steps, print a bunch of info and
// return the Lazy Beaver # if possible to conclude it. If outstream is
// non-NULL, write out all the not (yet) halted machines to that file.
long Enumerate(int num_states,
               int num_symbols,
               long max_steps,
               std::ostream* outstream = nullptr);

// Enumerate all TMs starting from the ones in instream.
// This can be used based on results written out by Enumerate().
//
// TODO: Figure out what to return and how to integrate all the returns from
// parallel runs.
void ContinueEnumerateFromFile(std::istream* instream);

}  // namespace lazy_beaver

#endif  // BUSY_BEAVER_LAZY_BEAVER_ENUMERATION_H_
