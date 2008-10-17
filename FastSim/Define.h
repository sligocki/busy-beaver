#ifndef _DEFINE_H_
#define _DEFINE_H_

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include <iostream>
#include <vector>

using namespace std;

#include "Exception.h"

typedef int Integer;

typedef struct
{
  int new_state;
  int new_symbol;
  int direction;
} TRANSITION;

extern void Warning(const char* const a_warning);
extern void Error(const char* const a_error);

#endif
