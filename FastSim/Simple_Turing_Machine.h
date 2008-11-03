#ifndef _SIMPLE_TURING_MACHINE_H_
#define _SIMPLE_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

class Simple_Turing_Machine: public Turing_Machine
{
  public:
    Simple_Turing_Machine(const TTable& a_ttable);

    virtual ~Simple_Turing_Machine();

    virtual RUN_STATE get_transition(TRANSITION&       a_trans_out,
                                     const TRANSITION& a_trans_in);

    TTable m_ttable;
};

#endif
