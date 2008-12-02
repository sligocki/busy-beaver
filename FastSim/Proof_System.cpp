#include "Expression.h"
#include "General_Chain_Simulator.h"
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

bool Proof_System::log(RUN_STATE     & a_run_state,
                       Tape<INTEGER> & a_new_tape,
                       INTEGER       & a_num_steps,
                       const CONFIG  & a_full_config)
{
  vector<int> stripped_config;
  strip_config(stripped_config,a_full_config.m_state,a_full_config.m_tape);

  if (m_proven_transitions.find(stripped_config) != m_proven_transitions.end())
  {
    bool bad_delta;
    if (applies(a_run_state,a_new_tape,a_num_steps,bad_delta,
                m_proven_transitions[stripped_config],a_full_config))
    {
      if ((!m_recursive || bad_delta) && m_prove_new_rules)
      {
        m_past_configs.clear();
      }

      return true;
    }

    return false;
  }

  if (!m_prove_new_rules)
  {
    return false;
  }

  if (m_past_configs.find(stripped_config) == m_past_configs.end())
  {
    PAST_CONFIG cur_config;
    cur_config.m_times_seen = 1;
    cur_config.m_config     = a_full_config;

    m_past_configs[stripped_config] = cur_config;

    return false;
  }

  PAST_CONFIG past_config = m_past_configs[stripped_config];

  if ((past_config.m_times_seen == 1) ||
      (a_full_config.m_loop_num - past_config.m_config.m_loop_num != past_config.m_delta_loop))
  {
    past_config.m_times_seen++;
    past_config.m_delta_loop = a_full_config.m_loop_num - past_config.m_config.m_loop_num;
    past_config.m_config     = a_full_config;

    m_past_configs[stripped_config] = past_config;

    return false;
  } 

  RULE rule;
  if (compare(rule,past_config.m_config,a_full_config))
  {
    m_proven_transitions[stripped_config] = rule;

    m_past_configs.clear();

    bool bad_delta;
    if (applies(a_run_state,a_new_tape,a_num_steps,bad_delta,
                rule,a_full_config))
    {
      return true;
    }
  }

  return false;
}

bool Proof_System::compare(RULE         & a_rule,
                           const CONFIG & a_old_config,
                           const CONFIG & a_new_config)
{
  Tape<Expression> gen_tape;

  gen_tape.m_init_symbol = a_old_config.m_tape.m_init_symbol;
  gen_tape.m_dir         = a_old_config.m_tape.m_dir;
  gen_tape.m_displace    = a_old_config.m_tape.m_displace;

  map<VARIABLE,INTEGER> min_val;

  for (int dir = 0; dir < 2; dir++)
  {
    const vector<Repeated_Symbol<INTEGER> >& old_half_tape = a_old_config.m_tape.m_half_tape[dir];
    vector<Repeated_Symbol<Expression> >& new_half_tape = gen_tape.m_half_tape[dir];
    for (int i = 0; i < old_half_tape.size(); i++)
    {
      const Repeated_Symbol<INTEGER> & old_repeated_symbol = old_half_tape[i];
      Repeated_Symbol<Expression> new_repeated_symbol;

      new_repeated_symbol.m_symbol = old_repeated_symbol.m_symbol;

      if (old_repeated_symbol.m_number != 1 &&
          old_repeated_symbol.m_number != INFINITY)
      {
        VARIABLE cur_var = new_var();

        Expression new_number(old_repeated_symbol.m_number,cur_var);
        new_repeated_symbol.m_number = new_number;

        min_val[cur_var] = old_repeated_symbol.m_number;
      }
      else
      {
        new_repeated_symbol.m_number = old_repeated_symbol.m_number;
      }

      new_half_tape.push_back(new_repeated_symbol);
    }
  }

  gen_tape.m_is_defined  = a_old_config.m_tape.m_is_defined;

  Tape<Expression> initial_tape = gen_tape;

  General_Chain_Simulator gen_sim(m_machine,false,false);
  gen_sim.m_tape = gen_tape;

  Error("Not implemented...");
}

bool Proof_System::applies(RUN_STATE     & a_run_state,
                           Tape<INTEGER> & a_new_tape,
                           INTEGER       & a_num_steps,
                           bool          & a_bad_delta,
                           const RULE    & a_rule,
                           const CONFIG  & a_full_config)
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
    for (vector<Repeated_Symbol<INTEGER> >::const_iterator it = a_tape.m_half_tape[side].begin();
         it != a_tape.m_half_tape[side].end();
         it++)
    {
      if (it->m_number == 1)
      {
        a_stripped_config.push_back(-(it->m_symbol));
      }
      else
      {
        a_stripped_config.push_back(it->m_symbol);
      }
    }
  }
}
