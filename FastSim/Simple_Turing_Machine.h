#ifndef _SIMPLE_TURING_MACHINE_H_
#define _SIMPLE_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

/// A Turing Machine based directly off of a transition table.
class Simple_Turing_Machine: public Turing_Machine
{
  public:
    Simple_Turing_Machine(const TTable & a_ttable);

    virtual ~Simple_Turing_Machine();

    virtual int eval_symbol(const SYMBOL & a_symbol);

    virtual int eval_state(const STATE & a_state);

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in);

    STATE  m_init_state;
    DIR    m_init_dir;
    SYMBOL m_init_symbol;
    
    int m_num_states;
    int m_num_symbols;
    
  private:
    TTable m_ttable;
};

#endif
