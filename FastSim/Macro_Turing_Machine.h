#ifndef _MACRO_TURING_MACHINE_H_
#define _MACRO_TURING_MACHINE_H_

#include "Define.h"
#include "TTable.h"
#include "Turing_Machine.h"

/// A derivative Turing Machine which simulates another machine clumping 
///   k-symbols together into a block-symbol.
class Macro_Turing_Machine: public Turing_Machine
{
  public:
    Macro_Turing_Machine(shared_ptr<Turing_Machine> a_machine,
                         const int                & a_block_size);

    virtual ~Macro_Turing_Machine();
    
    virtual int eval_symbol(const SYMBOL & a_symbol);
    
    virtual int eval_state(const STATE & a_state);

    virtual void get_transition(RUN_STATE        & a_run_state,
                                TRANSITION       & a_trans_out,
                                INTEGER          & a_num_steps,
                                const SYMBOL     & a_cur_symbol,
                                const TRANSITION & a_trans_in);

    STATE  m_init_state;
    DIR    m_init_dir;
    SYMBOL m_init_symbol;
    
    int m_num_states;
    int m_num_symbols;
    
    // Macro Machine specific fields
    int m_block_size;
    shared_ptr<Turing_Machine> m_base_machine;
    
    int m_max_steps;
};

#endif
