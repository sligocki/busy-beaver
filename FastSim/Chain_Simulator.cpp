#include "Chain_Simulator.h"

Chain_Simulator::Chain_Simulator(shared_ptr<Turing_Machine> a_machine,
                                 const bool               & a_recursive,
                                 const bool               & a_prover)
{
  m_inf_reason = NULL;

  m_num_loops = 0;

  m_num_macro_moves  = 0;
  m_steps_from_macro = 0;

  m_num_chain_moves  = 0;
  m_steps_from_chain = 0;

  m_num_rule_moves  = 0;
  m_steps_from_rule = 0;

  m_machine = a_machine;
  m_trans   = m_machine->m_init_trans;
  m_tape.define(m_machine->m_init_trans);

  m_step_num = 0;
  m_op_state = RUNNING;
  
  if (a_prover)
  {
    m_proof.define(m_machine,a_recursive);
  }
}

Chain_Simulator::~Chain_Simulator()
{
}

void Chain_Simulator::seek(const INTEGER & a_cutoff)
{
  while (m_step_num < a_cutoff && m_op_state == RUNNING)
  {
    step();
  }
}

void Chain_Simulator::step()
{
  if (m_op_state != RUNNING)
  {
    return;
  }

  m_num_loops++;

  INTEGER steps_in_proof;

  if (m_proof.m_is_defined)
  {
    RUN_STATE cond;
    Tape<INTEGER> new_tape;

    CONFIG full_config;
    full_config.m_state = m_trans.m_state;
    full_config.m_tape  = m_tape;
    full_config.m_step_num = m_step_num;
    full_config.m_loop_num = m_num_loops - 1;

    m_proof.log(cond,new_tape,steps_in_proof,full_config);

    if (cond == INFINITE)
    {
      m_op_state = INFINITE;
      m_inf_reason = "Proof_System";
      return;
    }
    else if (cond == RUNNING)
    {
      m_tape = new_tape;
      m_step_num += steps_in_proof;
      m_num_rule_moves++;
      m_steps_from_rule += steps_in_proof;
      return;
    }
  }

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
    INTEGER num_reps;
    num_reps = m_tape.apply_chain_move(new_trans.m_symbol);

    if (num_reps == INFINITY)
    {
      m_op_state = INFINITE;
      m_inf_reason = "Chain_Move";
    }
    else
    {
      m_step_num += steps_from_transition*num_reps;
      m_num_chain_moves++;
      m_steps_from_chain += steps_from_transition*num_reps;
    }
  }
  else
  {
    m_tape.apply_single_move(new_trans);
    m_trans = new_trans;
    m_step_num += steps_from_transition;
    m_num_macro_moves++;
    m_steps_from_macro += steps_from_transition;
    if (m_op_state == INFINITE)
    {
      m_inf_reason = "Repeat_in_Place";
    }
  }
}

INTEGER Chain_Simulator::num_nonzero()
{
  return m_tape.num_nonzero(m_machine,m_trans.m_state);
}

void Chain_Simulator::print(ostream & a_out) const
{
  a_out << "Total: " << m_step_num << ", " << m_num_loops << endl;
  a_out << "Macro: " << m_steps_from_macro << ", " << m_num_macro_moves << endl;
  a_out << "Chain: " << m_steps_from_chain << ", " << m_num_chain_moves << endl;

  if (m_proof.m_is_defined)
  {
    a_out << "Rule:  " << m_steps_from_rule << ", " << m_num_rule_moves << endl;
  }

  a_out << m_tape;

  a_out << endl;
}

ostream& operator<<(ostream               & a_ostream,
                    const Chain_Simulator & a_sim)
{
  a_sim.print(a_ostream);

  return a_ostream;
}
