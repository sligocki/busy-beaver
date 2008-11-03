#include "Simple_Turing_Machine.h"

Simple_Turing_Machine::Simple_Turing_Machine(const TTable& a_ttable)
{
  m_ttable = a_ttable;

  m_init_trans.state     = 0;
  m_init_trans.symbol    = 0;
  m_init_trans.direction = 1;
}

Simple_Turing_Machine::~Simple_Turing_Machine()
{
}

RUN_STATE Simple_Turing_Machine::get_transition(TRANSITION&       trans_out,
                                                const TRANSITION& trans_in)
{
  RUN_STATE run_state;

  trans_out = m_ttable.m_transitions[trans_in.state][trans_in.symbol];

  if (trans_out.symbol == -1)
  {
    run_state = UNDEFINED;
  }
  else if (trans_out.state == -1)
  {
    run_state = HALTED;
  }
  else
  {
    run_state = RUNNING;
  }

  return run_state;
}
