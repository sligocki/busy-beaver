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

    virtual int eval_symbol(const SYMBOL & a_symbol)
    {
      if (a_symbol != m_init_trans.m_symbol)
      {
        return 1;
      }
      else
      {
        return 0;
      }
    };

    virtual int eval_state(const STATE & a_state)
    {
      return 0;
    };

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in) = 0;

    int m_num_states;
    int m_num_symbols;

    TRANSITION m_init_trans;
};

#endif
