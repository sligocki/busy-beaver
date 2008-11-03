#include "Simple_Turing_Machine.h"

Simple_Turing_Machine::Simple_Turing_Machine(const TTable& a_ttable)
{
  m_ttable = a_ttable;

  m_init_trans.m_state  = 0;
  m_init_trans.m_symbol = 0;
  m_init_trans.m_dir    = 1;
}

Simple_Turing_Machine::~Simple_Turing_Machine()
{
}

RUN_STATE Simple_Turing_Machine::get_transition(TRANSITION&       a_trans_out,
                                                const TRANSITION& a_trans_in)
{
  RUN_STATE run_state;

  a_trans_out = m_ttable.m_transitions[a_trans_in.m_state][a_trans_in.m_symbol];

  if (a_trans_out.m_symbol == -1)
  {
    run_state = UNDEFINED;
  }
  else if (a_trans_out.m_state == -1)
  {
    run_state = HALTED;
  }
  else
  {
    run_state = RUNNING;
  }

  return run_state;
}
