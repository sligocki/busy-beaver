#ifndef _TURING_MACHINE_H_
#define _TURING_MACHINE_H_

#include "Define.h"

enum RUN_STATE {RUNNING, HALTED, INFINITE, UNDEFINED};

class Turing_Machine
{
  public:
    Turing_Machine()
    {
    };

    virtual ~Turing_Machine()
    {
    };

    /// The "sigma score" contribution from a symbol.
    /// For a normal Turing Machine, it is just 1 for any non-zero symbol.
    virtual int eval_symbol(const SYMBOL & a_symbol);

    /// The "sigma score" contribution from the state.
    /// This is normally nothing, but for Backsymbol Macro Machines store a 
    ///   symbol in the state and so the state contributes to the score.
    virtual int eval_state(const STATE & a_state);

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in) = 0;
    
    /// Start state and direction and blank symbol.
    STATE  m_init_state;
    DIR    m_init_dir;
    SYMBOL m_init_symbol;
    
    int m_num_states;
    int m_num_symbols;
};

#endif
