#ifndef _BLOCK_FINDER_H_
#define _BLOCK_FINDER_H_

#include "Define.h"
#include "Turing_Machine.h"

class Block_Finder
{
  public:
    Block_Finder(const Turing_Machine & a_machine);

    ~Block_Finder();

    int find_block();
};

#endif
