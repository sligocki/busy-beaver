#include "Proof_System.h"

Proof_System::Proof_System()
{
  m_is_defined = false;
}

Proof_System::~Proof_System()
{
  m_is_defined = false;
}

void Proof_System::define(shared_ptr<Turing_Machine> a_machine,
                          const bool               & a_recursive)
{
  m_machine   = a_machine;
  m_recursive = a_recursive;

  m_prove_new_rules = true;

  m_is_defined = true;
}

void Proof_System::log(RUN_STATE           & a_cond,
                       Tape<INTEGER>       & a_new_tape,
                       INTEGER             & a_num_steps,
                       const Tape<INTEGER> & a_old_tape,
                       const STATE         & a_old_state,
                       const INTEGER       & a_step_num,
                       const INTEGER       & a_loop_num)
{
  vector<int> stripped_config;
  strip_config(stripped_config,a_old_state,a_old_tape);

  if (m_proven_transitions.find(stripped_config) != m_proven_transitions.end())
  {
    bool is_good;
    TRANSITION trans;
    bool bad_delta;

    applies(is_good,trans,bad_delta,m_proven_transitions[stripped_config],
            a_old_tape,a_old_state,a_step_num,a_loop_num);
    
    if (is_good)
    {
      if ((!m_recursive || bad_delta) && m_prove_new_rules)
      {
        m_past_configs.clear();
      }
    }
  }

  Error("Not implemented...");
}

bool Proof_System::compare()
{
  Error("Not implemented...");
}

bool Proof_System::applies(bool                & a_is_good,
                           TRANSITION          & a_trans,
                           bool                & a_bad_delta,
                           const RULE          & a_rule,
                           const Tape<INTEGER> & a_new_tape,
                           const STATE         & a_new_state,
                           const INTEGER       & a_new_step_num,
                           const INTEGER       & a_new_loop_num)
{
  Error("Not implemented...");
}

void Proof_System::strip_config(vector<int>         & a_stripped_config,
                                const STATE         & a_state,
                                const Tape<INTEGER> & a_tape)
{
  a_stripped_config.push_back(a_state);
  a_stripped_config.push_back(a_tape.m_dir);

  for (int side = 0; side < 2; side++)
  {
    for (vector<repeated_symbol<INTEGER> >::const_iterator it = a_tape.m_tape[side].begin();
         it != a_tape.m_tape[side].end();
         it++)
    {
      a_stripped_config.push_back(it->m_symbol);
      if (it->m_number == 1)
      {
        a_stripped_config.push_back(1);
      }
    }
  }
}
