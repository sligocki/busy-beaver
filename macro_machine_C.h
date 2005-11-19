#include <Python.h>

#define PRIME_HASH_NUMBER   100003

typedef struct
{
  int w;
  int d;
  int s;
} TRANSITION;

typedef struct
{
  TRANSITION* t;
} STATE;

typedef struct
{
  int num_states;
  int num_symbols;

  STATE* machine;

  int* tape;
  int  tape_length;

  int symbol;

  int                total_symbols;
  unsigned long long total_steps;

  int position;
  int max_left;
  int max_right;

  int state;

  int new_symbol;
  int new_delta;
  int new_state;
} TM;

typedef struct macro_transition MACRO_TRANSITION;

struct macro_transition
{
  unsigned long long symbol;

  unsigned long long w;
  int d;
  int s;

  MACRO_TRANSITION* next;
};

typedef struct
{
  MACRO_TRANSITION** t;
} MACRO_STATE;

typedef struct
{
  int num_states;
  unsigned long long num_symbols;

  MACRO_STATE* machine;

  int* tape;
  int  tape_length;

  unsigned long long symbol;

  int                total_symbols;
  unsigned long long total_steps;

  int position;
  int max_left;
  int max_right;

  int state;

  unsigned long long new_symbol;
  int new_delta;
  int new_state;

  int size;
} MACRO_TM;
