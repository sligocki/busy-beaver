#include "General_Chain_Simulator.h"

General_Chain_Simulator::General_Chain_Simulator(shared_ptr<Turing_Machine> a_machine)
{
  m_inf_reason = NULL;

  m_num_loops = 0;

  m_machine = a_machine;
  m_trans   = m_machine->m_init_trans;
  m_tape.define(m_machine->m_init_trans);

  m_step_num = 0;
  m_op_state = RUNNING;
  
  // Needed for recursive proofs
  // if (a_prover)
  // {
  //   m_proof.define(m_machine,false);
  // }
}

General_Chain_Simulator::~General_Chain_Simulator()
{
}

void General_Chain_Simulator::step()
{
  if (m_op_state != RUNNING)
  {
    return;
  }

  m_num_loops++;

  Expression steps_in_proof;

  SYMBOL cur_symbol;
  cur_symbol = m_tape.get_top_symbol();

  INTEGER steps_from_transition;
  TRANSITION new_trans;
  m_machine->get_transition(m_op_state,new_trans,steps_from_transition,
                            cur_symbol,m_trans);

  if (new_trans.m_state == m_trans.m_state &&
      new_trans.m_dir   == m_trans.m_dir   &&
      m_op_state == RUNNING)
  {
    Expression num_reps;
    num_reps = m_tape.apply_chain_move(new_trans.m_symbol);

    if (num_reps == INFINITY)
    {
      m_op_state = INFINITE;
      m_inf_reason = "General_Chain_Move";
    }
    else
    {
      m_step_num += steps_from_transition*num_reps;
    }
  }
  else
  {
    m_tape.apply_single_move(new_trans);
    m_trans = new_trans;
    m_step_num += steps_from_transition;
    if (m_op_state == INFINITE)
    {
      m_inf_reason = "Repeat_in_Place";
    }
  }
}

void General_Chain_Simulator::print(ostream & a_out) const
{
  a_out << "Total: " << m_step_num << ", " << m_num_loops << endl;

  a_out << endl;
}

ostream& operator<<(ostream                       & a_ostream,
                    const General_Chain_Simulator & a_sim)
{
  a_sim.print(a_ostream);

  return a_ostream;
}
