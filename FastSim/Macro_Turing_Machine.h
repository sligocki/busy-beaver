#ifndef _MACRO_TURING_MACHINE_H_
#define _MACRO_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Macro_Turing_Machine: public Turing_Machine
{
  public:
    Macro_Turing_Machine(shared_ptr<Turing_Machine> a_machine,
                         const int                & a_block_size);

    virtual ~Macro_Turing_Machine();

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in);
};

#endif
