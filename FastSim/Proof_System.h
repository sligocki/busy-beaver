#ifndef _PROOF_SYSTEM_H_
#define _PROOF_SYSTEM_H_

#include "Define.h"
#include "Turing_Machine.h"

class Proof_System
{
  public:
    Proof_System();

    ~Proof_System();

    void define(const Turing_Machine& a_machine,
                const bool&           a_recursive);

    bool log();

    bool compare();

    bool applies();
};

#endif
