#ifndef _GENERAL_CHAIN_SIMULATOR_H_
#define _GENERAL_CHAIN_SIMULATOR_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"
// This would need to be added back for recursive proofs
// #include "General_Proof_System.h"
#include "Expression.h"

class General_Chain_Simulator
{
  public:
    General_Chain_Simulator(shared_ptr<Turing_Machine> a_machine);

    virtual ~General_Chain_Simulator();

    void step();

    void print(ostream & a_out) const;

    const char* m_inf_reason;

    INTEGER m_num_loops;

    shared_ptr<Turing_Machine> m_machine;

    TRANSITION       m_trans;
    Tape<Expression> m_tape;

    Expression m_step_num;
    RUN_STATE  m_op_state;

    // This would need to be added back for recursive proofs
    // General_Proof_System m_proof;
};

ostream& operator<<(ostream                       & a_ostream,
                    const General_Chain_Simulator & a_sim);

#endif
