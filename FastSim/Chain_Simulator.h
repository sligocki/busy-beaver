#ifndef _CHAIN_SIMULATOR_H_
#define _CHAIN_SIMULATOR_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"
#include "Proof_System.h"

class Chain_Simulator
{
  public:
    Chain_Simulator(const Turing_Machine& a_machine,
                    const bool          & a_recursive,
                    const bool          & a_prover);

    virtual ~Chain_Simulator();

    void seek(const Integer& a_extent);

    RUN_STATE run_state();

    Integer num_steps();

    Integer num_nonzero();

    char* inf_reason();

    int cur_state();
    int cur_symbol();

    void print();

    Integer m_num_loops;

    Integer m_num_macro_moves;
    Integer m_steps_from_macro;

    Integer m_num_chain_moves;
    Integer m_steps_from_chain;

    Integer m_num_rule_moves;
    Integer m_steps_from_rule;

    Turing_Machine m_machine;
    TRANSITION     m_trans;
    Tape           m_tape;

    Integer   m_step_num;
    RUN_STATE m_op_state;

    Proof_System m_proof;
};

#endif
