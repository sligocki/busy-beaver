#ifndef _GENERAL_CHAIN_SIMULATOR_H_
#define _GENERAL_CHAIN_SIMULATOR_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"
#include "General_Proof_System.h"
#include "Expression.h"

class General_Chain_Simulator
{
  public:
    General_Chain_Simulator(shared_ptr<Turing_Machine> a_machine,
                            const bool               & a_recursive,
                            const bool               & a_prover);

    virtual ~General_Chain_Simulator();

    void step();

    INTEGER num_nonzero();

    void print(ostream & a_out) const;

    const char* m_inf_reason;

    INTEGER m_num_loops;

    shared_ptr<Turing_Machine> m_machine;

    TRANSITION       m_trans;
    Tape<Expression> m_tape;

    Expression m_step_num;
    RUN_STATE  m_op_state;

    General_Proof_System m_proof;
};

ostream& operator<<(ostream                       & a_ostream,
                    const General_Chain_Simulator & a_sim);

#endif
