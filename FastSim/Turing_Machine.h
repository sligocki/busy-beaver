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

    virtual int eval_symbol(const int& a_symbol)
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

    virtual int eval_state(const int& a_state)
    {
      return 0;
    };

    virtual RUN_STATE get_transition(TRANSITION&       trans_out,
                                     const TRANSITION& trans_in)
    {
      Error("Not implemented...");
    };

    int m_num_states;
    int m_num_symbols;

    TRANSITION m_init_trans;
};

#endif
