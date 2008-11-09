#include "Simple_Turing_Machine.h"

Simple_Turing_Machine::Simple_Turing_Machine(const TTable & a_ttable)
{
  m_ttable = a_ttable;

  m_init_trans.m_state  = 0;
  m_init_trans.m_symbol = 0;
  m_init_trans.m_dir    = 1;
}

Simple_Turing_Machine::~Simple_Turing_Machine()
{
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
}
