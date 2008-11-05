#include "Chain_Simulator.h"

Chain_Simulator::Chain_Simulator(const Turing_Machine& a_machine,
                                 const bool          & a_recursive,
                                 const bool          & a_prover)
{
  m_num_loops = 0;

  m_num_macro_moves  = 0;
  m_steps_from_macro = 0;

  m_num_chain_moves  = 0;
  m_steps_from_chain = 0;

  m_num_rule_moves  = 0;
  m_steps_from_rule = 0;

  m_machine = a_machine;
  m_trans   = m_machine.m_init_trans;
  m_tape.define(m_machine.m_init_trans);

  m_step_num = 0;
  m_op_state = RUNNING;
  
  if (a_prover)
  {
    m_proof.define(m_machine,a_recursive);
  }
}

Chain_Simulator::~Chain_Simulator()
{
  Error("Not implemented...");
}

void Chain_Simulator::seek(const INTEGER& a_extent)
{
  Error("Not implemented...");
}

RUN_STATE Chain_Simulator::run_state()
{
  Error("Not implemented...");
}

INTEGER Chain_Simulator::num_steps()
{
  Error("Not implemented...");
}

INTEGER Chain_Simulator::num_nonzero()
{
  Error("Not implemented...");
}

char* Chain_Simulator::inf_reason()
{
  Error("Not implemented...");
}

STATE Chain_Simulator::cur_state()
{
  Error("Not implemented...");
}

SYMBOL Chain_Simulator::cur_symbol()
{
  Error("Not implemented...");
}

void Chain_Simulator::print()
{
  Error("Not implemented...");
}
