#ifndef _PROOF_SYSTEM_H_
#define _PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"

typedef struct {
  Tape<INTEGER> m_initial_tape;
  Tape<INTEGER> m_diff_tape;
  INTEGER       m_diff_num_steps;
} RULE;

typedef struct {
  STATE         m_state;
  Tape<INTEGER> m_tape;
  INTEGER       m_step_num;
  INTEGER       m_loop_num;
} CONFIG;

typedef struct {
  int     m_times_seen;
  INTEGER m_delta_loop;
  CONFIG  m_config;
} PAST_CONFIG;

class Proof_System
{
  public:
    Proof_System();

    ~Proof_System();

    void define(shared_ptr<Turing_Machine> a_machine,
                const bool               & a_recursive);

    bool log(RUN_STATE     & a_run_state,
             Tape<INTEGER> & a_new_tape,
             INTEGER       & a_num_steps,
             const CONFIG  & a_full_config);

    bool compare(RULE              & a_rule,
                 const PAST_CONFIG & a_past_config,
                 const CONFIG      & a_full_config);

    bool applies(RUN_STATE     & a_run_state,
                 Tape<INTEGER> & a_new_tape,
                 INTEGER       & a_num_steps,
                 bool          & a_bad_delta,
                 const RULE    & a_rule,
                 const CONFIG  & a_full_config);

    void strip_config(vector<int>         & a_stripped_config,
                      const STATE         & a_state,
                      const Tape<INTEGER> & a_tape);

    shared_ptr<Turing_Machine> m_machine;

    bool m_recursive;
    bool m_prove_new_rules;

    map<vector<int>,RULE>        m_proven_transitions;
    map<vector<int>,PAST_CONFIG> m_past_configs;

    bool m_is_defined;
};

#endif
