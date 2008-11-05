#ifndef _TAPE_H_
#define _TAPE_H_

#include "Define.h"

typedef struct
{
  SYMBOL  m_symbol;
  INTEGER m_number;
} REPEATED_SYMBOL;

#define INFINITY -1

class Tape
{
  public:
    Tape();

    ~Tape();

    void define(const TRANSITION& a_init_trans);

    INTEGER get_nonzeros(const INTEGER& a_state_value);

    REPEATED_SYMBOL get_top_block();

    SYMBOL get_top_symbol();

    void apply_single_move(const SYMBOL& a_new_symbol,
                           const int&    a_dir);

    INTEGER apply_chain_move(const SYMBOL& a_new_symbol);

    SYMBOL m_init_symbol;
    int    m_dir;

    vector<REPEATED_SYMBOL> m_tape[2];

    INTEGER m_displace;

    bool m_is_defined;
};

#endif
