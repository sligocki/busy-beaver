#ifndef _GENERAL_PROOF_SYSTEM_H_
#define _GENERAL_PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"
#include "Proof_System.h"

class General_Proof_System
{
  public:
    General_Proof_System();

    ~General_Proof_System();

    void define(shared_ptr<Turing_Machine> a_machine,
                const bool               & a_recursive);

    bool log(RUN_STATE     & a_run_state,
             Tape<INTEGER> & a_new_tape,
             INTEGER       & a_num_steps,
             const CONFIG  & a_full_config);

    bool compare(RULE         & a_rule,
                 const CONFIG & a_old_config,
                 const CONFIG & a_new_config);

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
