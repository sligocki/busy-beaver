#ifndef _SIMPLE_TURING_MACHINE_H_
#define _SIMPLE_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Simple_Turing_Machine: public Turing_Machine
{
  public:
    Simple_Turing_Machine(const TTable & a_ttable);

    virtual ~Simple_Turing_Machine();

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in);

    TTable m_ttable;
};

#endif
