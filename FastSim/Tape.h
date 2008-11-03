#ifndef _TAPE_H_
#define _TAPE_H_

#include "Define.h"

typedef struct
{
  int     symbol;
  Integer number;
} REPEATED_SYMBOL;

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

    void apply_chain_move(const int& a_new_symbol);
};

#endif
