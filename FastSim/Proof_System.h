#ifndef _PROOF_SYSTEM_H_
#define _PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"

typedef struct {
  Tape<INTEGER> m_initial_tape;
  Tape<INTEGER> m_diff_tape;
  INTEGER   m_diff_num_steps;
} RULE;

class Proof_System
{
  public:
    Proof_System();

    ~Proof_System();

    void define(shared_ptr<Turing_Machine> a_machine,
                const bool               & a_recursive);

    bool log(RUN_STATE           & a_run_state,
             Tape<INTEGER>       & a_new_tape,
             INTEGER             & a_num_steps,
             const Tape<INTEGER> & a_old_tape,
             const STATE         & a_old_state,
             const INTEGER       & a_step_num,
             const INTEGER       & a_loop_num);

    bool compare();

    bool applies(RUN_STATE           & a_run_state,
                 Tape<INTEGER>       & a_new_tape,
                 INTEGER             & a_num_steps,
                 bool                & a_bad_delta,
                 const RULE          & a_rule,
                 const Tape<INTEGER> & a_old_tape,
                 const STATE         & a_old_state,
                 const INTEGER       & a_step_num,
                 const INTEGER       & a_loop_num);

    void strip_config(vector<int>         & a_stripped_config,
                      const STATE         & a_state,
                      const Tape<INTEGER> & a_tape);

    shared_ptr<Turing_Machine> m_machine;

    bool m_recursive;
    bool m_prove_new_rules;

    map<vector<int>,vector<int> > m_past_configs;
    map<vector<int>,RULE>         m_proven_transitions;

    bool m_is_defined;
};

#endif
