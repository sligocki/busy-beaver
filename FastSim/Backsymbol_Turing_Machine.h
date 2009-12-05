#ifndef _BACKSYMBOL_TURING_MACHINE_H_
#define _BACKSYMBOL_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Backsymbol_Turing_Machine: public Turing_Machine
{
  public:
    Backsymbol_Turing_Machine(shared_ptr<Turing_Machine> a_machine);

    virtual ~Backsymbol_Turing_Machine();

    virtual int eval_symbol(const SYMBOL & a_symbol);

    virtual int eval_state(const STATE & a_state);

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in);
};

#endif
