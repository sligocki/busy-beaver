#ifndef _TAPE_H_
#define _TAPE_H_

#include "Define.h"

typedef struct
{
  int     m_symbol;
  Integer m_number;
} REPEATED_SYMBOL;

#define INFINITY -1

class Tape
{
  public:
    Tape();

    ~Tape();

    void define(const TRANSITION& a_init_trans);

    Integer get_nonzeros(const Integer& a_state_value);

    REPEATED_SYMBOL get_top_block();

    int get_top_symbol();

    void apply_single_move(const int& a_new_symbol,
                           const int& a_dir);

    Integer apply_chain_move(const int& a_new_symbol);

    int m_init_symbol;
    int m_dir;

    vector<REPEATED_SYMBOL> m_tape[2];

    Integer m_displace;

    bool m_is_defined;
};

#endif
