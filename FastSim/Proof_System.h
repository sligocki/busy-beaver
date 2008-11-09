#ifndef _PROOF_SYSTEM_H_
#define _PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"

typedef struct {
  Tape    m_initial_tape;
  Tape    m_diff_tape;
  INTEGER m_diff_num_steps;
} RULE;

class Proof_System
{
  public:
    Proof_System();

    ~Proof_System();

    void define(shared_ptr<Turing_Machine> a_machine,
                const bool               & a_recursive);

    void log(RUN_STATE     & a_cond,
             Tape          & a_new_tape,
             INTEGER       & a_num_steps,
             const Tape    & a_old_tape,
             const STATE   & a_old_state,
             const INTEGER & a_step_num,
             const INTEGER & a_loop_num);

    bool compare();

    bool applies(bool          & a_is_good,
                 TRANSITION    & a_trans,
                 bool          & a_bad_delta,
                 const RULE    & a_rule,
                 const Tape    & a_new_tape,
                 const STATE   & a_new_state,
                 const INTEGER & a_new_step_num,
                 const INTEGER & a_new_loop_num);

    void strip_config(vector<int> & a_stripped_config,
                      const STATE & a_state,
                      const Tape  & a_tape);

    shared_ptr<Turing_Machine> m_machine;

    bool m_recursive;

    map<vector<int>,vector<int> > m_past_configs;
    map<vector<int>,RULE>         m_proven_transitions;

    bool m_is_defined;
};

#endif
