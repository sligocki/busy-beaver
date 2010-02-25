#ifndef _DEFINE_H_
#define _DEFINE_H_

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include <iostream>
#include <vector>
#include <map>

#include <boost/shared_ptr.hpp>

#include <assert.h>
#include <gmpxx.h>

using namespace std;
using namespace boost;

#include "Exception.h"

// typedef int INTEGER;
// typedef long long INTEGER;
typedef mpz_class INTEGER;

typedef int STATE;
typedef int SYMBOL;

enum DIR {LEFT, RIGHT};

typedef struct
{
  STATE  m_state;
  SYMBOL m_symbol;
  DIR    m_dir;
} TRANSITION;

#endif
