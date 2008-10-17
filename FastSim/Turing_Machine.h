#ifndef _TURING_MACHINE_H_
#define _TURING_MACHINE_H_

#include "Define.h"

class Turing_Machine
{
  public:
    enum run_state {RUNNING, HALT, INFINITE, UNDEFINED};

    Turing_Machine();

    virtual ~Turing_Machine();
};

#endif
