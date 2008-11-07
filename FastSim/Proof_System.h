#ifndef _PROOF_SYSTEM_H_
#define _PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"
#include "Tape.h"

class Proof_System
{
  public:
    Proof_System();

    ~Proof_System();

    void define(const Turing_Machine& a_machine,
                const bool&           a_recursive);

    void log(RUN_STATE&     a_cond,
             Tape&          a_new_tape,
             INTEGER&       a_num_steps,
             const Tape&    a_old_tape,
             const STATE&   a_old_state,
             const INTEGER& a_step_num,
             const INTEGER& a_loop_num);

    bool compare();

    bool applies();

    Turing_Machine m_machine;
    bool           m_recursive;

    map<vector<SYMBOL>,vector<int> > m_past_configs;
    map<vector<SYMBOL>,bool>         m_proven_transitions;

    bool m_is_defined;
};

#endif
