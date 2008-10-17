#ifndef _MACRO_TURING_MACHINE_H_
#define _MACRO_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Macro_Turing_Machine: public Turing_Machine
{
  public:
    Macro_Turing_Machine(const Turing_Machine& a_machine,
                         const int           & a_block_size);

    virtual ~Macro_Turing_Machine();
};

#endif
