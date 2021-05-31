#define PRIME_HASH_NUMBER   100003

typedef struct macro_transition MACRO_TRANSITION;

struct macro_transition
{
  int* symbol;

  int* w;
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

  int* symbol;

  unsigned long long total_symbols;
  unsigned long long total_steps;

  int position;
  int max_left;
  int max_right;

  int state;

  int* new_symbol;
  int new_delta;
  int new_state;

  int size;
} MACRO_TM;
