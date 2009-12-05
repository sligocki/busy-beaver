#include "Simple_Turing_Machine.h"

Simple_Turing_Machine::Simple_Turing_Machine(const TTable & a_ttable)
{
  m_ttable = a_ttable;
  
  m_num_states  = m_ttable.m_num_states;
  m_num_symbols = m_ttable.m_num_symbols;
  
  m_init_state = 0;
  m_init_dir = LEFT;
  m_init_symbol = 0;
}

Simple_Turing_Machine::~Simple_Turing_Machine()
{
}

// The "sigma score" contribution from a symbol.
// For a normal Turing Machine, it is just 1 for any non-zero symbol.
int Simple_Turing_Machine::eval_symbol(const SYMBOL & a_symbol);
{
  if (a_symbol != m_init_trans.m_symbol)
  {
    return 1;
  }
  else
  {
    return 0;
  }
}

// The "sigma score" contribution from the state.
// Simple TMs contribute nothing from state.
int Simple_Turing_Machine::eval_state(const STATE & a_state)
{
  return 0;
}

void Simple_Turing_Machine::get_transition(RUN_STATE        & a_run_state,
                                           TRANSITION       & a_trans_out,
                                           INTEGER          & a_num_steps,
                                           const SYMBOL     & a_cur_symbol,
                                           const TRANSITION & a_trans_in)
{
  a_trans_out = m_ttable.m_transitions[a_trans_in.m_state][a_cur_symbol];

  if (a_trans_out.m_symbol == -1)
  {
    a_run_state = UNDEFINED;
  }
  else if (a_trans_out.m_state == -1)
  {
    a_run_state = HALTED;
  }
  else
  {
    a_run_state = RUNNING;
  }

  a_num_steps = 1;
}
