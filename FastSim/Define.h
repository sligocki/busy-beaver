#ifndef _DEFINE_H_
#define _DEFINE_H_

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include <iostream>
#include <vector>
#include <map>

using namespace std;

#include "Exception.h"

typedef int INTEGER;

typedef int STATE;
typedef int SYMBOL;

typedef struct
{
  STATE  m_state;
  SYMBOL m_symbol;
  int    m_dir;
} TRANSITION;

#endif
