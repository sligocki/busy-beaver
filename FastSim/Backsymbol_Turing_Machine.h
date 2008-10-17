#ifndef _BACKSYMBOL_TURING_MACHINE_H_
#define _BACKSYMBOL_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Backsymbol_Turing_Machine: public Turing_Machine
{
  public:
    Backsymbol_Turing_Machine(const Turing_Machine& a_machine);

    virtual ~Backsymbol_Turing_Machine();
};

#endif
