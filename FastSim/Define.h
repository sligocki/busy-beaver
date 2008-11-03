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
  int state;
  int symbol;
  int direction;
} TRANSITION;

#endif
