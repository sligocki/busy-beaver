#define RESULT_MACHINE        0x0003
#define RESULT_M1             0x0000
#define RESULT_M2             0x0001
#define RESULT_BOTH           0x0002

#define RESULT_VALUE          0x003C
#define RESULT_STEPPED        0x0000
#define RESULT_UNDEFINED      0x0004
#define RESULT_HALTED         0x0008
#define RESULT_NOTAPE         0x000C
#define RESULT_INFINITE_LEFT  0x0010
#define RESULT_INFINITE_RIGHT 0x0014
#define RESULT_INFINITE_DUAL  0x0018
#define RESULT_INFINITE_TREE  0x001C
#define RESULT_INVALID        0x0020

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
  unsigned long long tape_length;

  int symbol;

  unsigned long long total_symbols;
  unsigned long long total_steps;

  unsigned long long position;
  unsigned long long max_left;
  unsigned long long max_right;

  int state;

  int new_symbol;
  int new_delta;
  int new_state;
} TM;

extern inline int  step_TM (TM* m);
extern inline int  step_recur_TM (TM* m, int step_num);
extern inline void print_TM(TM* m);
extern inline void free_TM (TM* m);
