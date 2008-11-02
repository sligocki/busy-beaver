#ifndef _TURING_MACHINE_H_
#define _TURING_MACHINE_H_

#include "Define.h"

class Turing_Machine
{
  public:
    enum run_state {RUNNING, HALT, INFINITE, UNDEFINED};

    Turing_Machine()
    {
    };

    virtual ~Turing_Machine()
    {
    };

    virtual bool eval_symbol(const int& a_symbol)
    {
      return (a_symbol != m_init_symbol);
    };

    virtual bool eval_state(const int& a_state)
    {
      return false;
    };

    virtual void get_transition(const int& a_state_in,
                                const int& a_symbol_in,
                                const int& a_dir_in)
    {
      Error("Not implemented...");
    };

    int m_num_states;
    int m_num_symbols;

    int m_init_state;
    int m_init_symbol;
    int m_init_dir;
};

#endif
