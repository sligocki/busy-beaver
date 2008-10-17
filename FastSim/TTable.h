#ifndef _TTABLE_H_
#define _TTABLE_H_

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace std;

#include "Define.h"

class TTable
{
  public:
    TTable();

    ~TTable();
    
    void clear();

    void define(const int                        & a_num_states,
                const int                        & a_num_symbols,
                const vector<vector<TRANSITION> >& a_transitions);

    bool read(FILE* a_file);

    int m_num_states;
    int m_num_symbols;

    TRANSITION** m_transitions;

    bool m_is_defined;
};

#endif
