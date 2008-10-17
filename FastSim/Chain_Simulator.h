#ifndef _CHAIN_SIMULATOR_H_
#define _CHAIN_SIMULATOR_H_

#include "Define.h"
#include "Turing_Machine.h"

class Chain_Simulator
{
  public:
    Chain_Simulator(const Turing_Machine& a_machine,
                    const bool          & a_recursive,
                    const bool          & a_prover);

    virtual ~Chain_Simulator();

    void seek(const Integer& a_extent);

    Turing_Machine::run_state run_state();

    Integer num_steps();

    Integer num_nonzero();

    char* inf_reason();

    int cur_state();
    int cur_symbol();

    void print();
};

#endif
