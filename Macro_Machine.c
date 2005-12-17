#include "Macro_Machine.h"

static PyObject* Macro_Machine_Run(PyObject* self,
                                   PyObject* args);

static PyMethodDef Macro_Machine_Methods[] =
{
  { "run", Macro_Machine_Run, METH_VARARGS, "Run Turing machine" },
  { NULL , NULL             , 0           , NULL                 }
};

PyMODINIT_FUNC initMacro_Machine(void)
{
  (void)Py_InitModule("Macro_Machine",Macro_Machine_Methods);
}

#define RESULT_MACHINE        0x0003
#define RESULT_M1             0x0000
#define RESULT_M2             0x0001
#define RESULT_BOTH           0x0002

#define RESULT_VALUE          0x001C
#define RESULT_STEPPED        0x0000
#define RESULT_UNDEFINED      0x0004
#define RESULT_HALTED         0x0008
#define RESULT_NOTAPE         0x000C
#define RESULT_INFINITE_LEFT  0x0010
#define RESULT_INFINITE_RIGHT 0x0014
#define RESULT_INFINITE_DUAL  0x0018

inline void print_TM(TM* m)
{
  int state,symbol;

  fprintf(stderr,"machine, (%d %4d)\n",
          m->num_states,m->num_symbols);
  for (state = 0; state < m->num_states; state++)
  {
    fprintf(stderr,"  State: %d\n",state);
    for (symbol = 0; symbol < m->num_symbols; symbol++)
    {
      fprintf(stderr,"    Symbol: %4d -> ",symbol);
      fprintf(stderr,"%4d ",m->machine[state].t[symbol].w);
      fprintf(stderr,"%2d ",m->machine[state].t[symbol].d);
      fprintf(stderr,"%2d\n",m->machine[state].t[symbol].s);
    }
  }
}

inline int step_TM(TM* m)
{
  m->total_steps++;

  m->new_symbol = m->machine[m->state].t[m->symbol].w;
  m->new_delta  = m->machine[m->state].t[m->symbol].d;
  m->new_state  = m->machine[m->state].t[m->symbol].s;

  if (m->new_symbol == -1)
  {
    return RESULT_UNDEFINED;
  }

  if (m->symbol == 0 && m->new_symbol != 0) {
    m->total_symbols++;
  }

  if (m->symbol != 0 && m->new_symbol == 0)
  {
    m->total_symbols--;
  }

  m->tape[m->position] = m->new_symbol;
  m->position += m->new_delta;

  if (m->new_state == -1)
  {
    return RESULT_HALTED;
  }

  if (m->position < 1 || m->position >= m->tape_length-1)
  {
    return RESULT_NOTAPE;
  }
  
  m->symbol = m->tape[m->position];
  m->state = m->new_state;

  return RESULT_STEPPED;
}

inline void get_macro_symbol(int* symbol, int* tape, int position, int size)
{
  int i;
  for (i = 0; i < 2*size+1; i++)
  {
    symbol[i] = tape[i + position-size];
  }
}

inline void put_macro_symbol(int* symbol, int* tape, int position, int size)
{
  int i;
  for (i = 0; i < 2*size+1; i++)
  {
    tape[i + position-size] = symbol[i];
  }
}

inline int equal_symbol(int* symbol1, int* symbol2, int size)
{
  int i;
  int equal = 1;

  for (i = 0; i < 2*size+1; i++)
  {
    if (symbol1[i] != symbol2[i])
    {
      equal = 0;
      break;
    }
  }

  return equal;
}

inline MACRO_TRANSITION* hash_lookup(MACRO_TM* m, int state, int* symbol, int orig_num_symbols)
{
  int hash_index;
  int i;
  MACRO_TRANSITION* trans;

  hash_index = 0;
  for (i = 0; i < 2*m->size+1; i++)
  {
    hash_index = (hash_index*orig_num_symbols + symbol[i]) % PRIME_HASH_NUMBER;
  }

  trans = m->machine[state].t[hash_index];

  while (trans != NULL)
  {
    if (equal_symbol(trans->symbol,symbol,m->size))
    {
      break;
    }

    trans = trans->next;
  }

  return trans;
}

inline MACRO_TRANSITION* hash_add(MACRO_TM* m, int state, int* symbol, TM* baseTM)
{
  int i;
  int hash_index;
  MACRO_TRANSITION* trans;

  int start;
  int step;

  int result;

  hash_index = 0;
  for (i = 0; i < 2*m->size+1; i++)
  {
    hash_index = (hash_index*baseTM->num_symbols + symbol[i]) % PRIME_HASH_NUMBER;
  }

  trans = (MACRO_TRANSITION *)malloc(sizeof(*trans));

  trans->symbol = (int *)malloc((2*m->size+1) * sizeof(*(trans->symbol)));
  for (i = 0; i < 2*m->size+1; i++)
  {
    trans->symbol[i] = symbol[i];
  }

  trans->w = (int *)malloc((2*m->size+1) * sizeof(*(trans->w)));

  trans->next = m->machine[state].t[hash_index];
  m->machine[state].t[hash_index] = trans;

  baseTM->tape[0                    ] = 0;
  baseTM->tape[1                    ] = 0;
  baseTM->tape[baseTM->tape_length-2] = 0;
  baseTM->tape[baseTM->tape_length-1] = 0;

  baseTM->position  = (baseTM->tape_length-1) / 2;
  put_macro_symbol(symbol,baseTM->tape,baseTM->position,m->size);

  baseTM->max_left  = (baseTM->tape_length-1) / 2;
  baseTM->max_right = (baseTM->tape_length-1) / 2;

  baseTM->total_symbols = 0;
  baseTM->total_steps   = 0;

  baseTM->state  = state;
  baseTM->symbol = baseTM->tape[baseTM->position];

  start = baseTM->position;

  for (step = 0; step <= m->size; step++)
  {
    result = step_TM(baseTM);

    if (result != RESULT_STEPPED)
    {
      if (result != RESULT_UNDEFINED)
      {
        fprintf(stderr,"Unexpected TM result: %d\n",result);
        print_TM(baseTM);
      }

      break;
    }
  }

  if (result == RESULT_STEPPED)
  {
    get_macro_symbol(trans->w, baseTM->tape, start, m->size);
    trans->d = baseTM->position-start;
    trans->s = baseTM->state;
  }
  else
  {
    int i;
    for (i = 0; i < 2*m->size+1; i++)
    {
      trans->w[i] = -1;
    }

    trans->d = -1;
    trans->s = -1;
  }

  return trans;
}

inline int step_macro_TM(MACRO_TM* m, TM* baseTM)
{
  int i;
  MACRO_TRANSITION* trans;

  m->total_steps += m->size;

  trans = hash_lookup(m,m->state,m->symbol,baseTM->num_symbols);

  if (trans == NULL)
  {
    trans = hash_add(m,m->state,m->symbol,baseTM);
  }

  for (i = 0; i < 2*m->size+1; i++)
  {
    m->new_symbol[i] = trans->w[i];
  }

  m->new_delta  = trans->d;
  m->new_state  = trans->s;

  if (m->new_symbol[0] == -1)
  {
    return RESULT_UNDEFINED;
  }

  if (m->symbol == 0 && m->new_symbol != 0) {
    m->total_symbols++;
  }

  if (m->symbol != 0 && m->new_symbol == 0)
  {
    m->total_symbols--;
  }

  put_macro_symbol(m->new_symbol,m->tape,m->position,m->size);
  m->position += m->new_delta;

  if (m->new_state == -1)
  {
    return RESULT_HALTED;
  }

  if (m->position < m->size || m->position >= m->tape_length - m->size)
  {
    return RESULT_NOTAPE;
  }
  
  get_macro_symbol(m->new_symbol,m->tape,m->position,m->size);

  if (m->position < m->max_left)
  {
    m->max_left = m->position;

    if (equal_symbol(m->new_symbol,m->symbol,m->size) && m->new_state == m->state && m->new_delta < 0)
    {
      return RESULT_INFINITE_LEFT;
    }
  }

  if (m->position > m->max_right)
  {
    m->max_right = m->position;

    if (equal_symbol(m->new_symbol,m->symbol,m->size) && m->new_state == m->state && m->new_delta > 0)
    {
      return RESULT_INFINITE_RIGHT;
    }
  }

  for (i = 0; i < 2*m->size+1; i++)
  {
    m->symbol[i] = m->new_symbol[i];
  }

  m->state = m->new_state;

  return RESULT_STEPPED;
}

static PyObject* Macro_Machine_Run(PyObject* self,
                                   PyObject* args)
{
  TM inTM;
  MACRO_TM macroTM;

  int result;

  double d_total_symbols;
  double d_total_steps;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;
  STATE* inMachine = NULL;
  MACRO_STATE* macroMachine = NULL;

  PyObject* num_states_obj;
  int num_states,num_states_imp;

  PyObject* num_symbols_obj;
  int num_symbols,num_symbols_imp;

  PyObject* tape_length_obj;

  PyObject* macro_size_obj;
  int macro_size;

  PyObject* max_steps_obj;
  unsigned long long max_steps;

  int state;

  if (!PyTuple_CheckExact(args))
  {
    return Py_BuildValue("(iis)",-1,0,"Argument_was_not_a_tuple");
  }

  n_tuple = PyTuple_Size(args);

  if (n_tuple != 6)
  {
    return Py_BuildValue("(iis)",-1,1,"Expected_a_6-tuple_argument");
  }

  machine_obj = PyTuple_GetItem(args,0);
  if (machine_obj == NULL || !PyList_Check(machine_obj))
  {
    return Py_BuildValue("(iis)",-1,2,"Unable_to_extract_Turing_machine");
  }

  num_states_obj = PyTuple_GetItem(args,1);
  if (num_states_obj == NULL || !PyInt_CheckExact(num_states_obj))
  {
    return Py_BuildValue("(iis)",-1,3,"Unable_to_extract_#_of_states");
  }

  num_states = PyInt_AsLong(num_states_obj);

  num_symbols_obj = PyTuple_GetItem(args,2);
  if (num_symbols_obj == NULL || !PyInt_CheckExact(num_symbols_obj))
  {
    return Py_BuildValue("(iis)",-1,4,"Unable_to_extract_#_of_symbols");
  }

  num_symbols = PyInt_AsLong(num_symbols_obj);

  macro_size_obj = PyTuple_GetItem(args,3);

  if (macro_size_obj == NULL || !PyInt_CheckExact(macro_size_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_macro_size");
  }

  macro_size = PyInt_AsLong(macro_size_obj);
  macroTM.size = macro_size;

  num_states_imp = PyList_Size(machine_obj);

  if (num_states_imp != num_states)
  {
    return Py_BuildValue("(iis)",-1,5,"Number_of_states_do_not_match");
  }

  inMachine = (STATE *)malloc(num_states*sizeof(*inMachine));

  if (inMachine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_machine");
  }

  {
    int iter_state;
    for (iter_state = 0; iter_state < num_states; iter_state++)
    {
      int iter_symbol;
      PyObject* cur_state_obj;

      cur_state_obj = PyList_GetItem(machine_obj,iter_state);
      if (!PyList_Check(cur_state_obj))
      {
        return Py_BuildValue("(iis)",-1,7,"Unable_to_extract_Turing_machine_transition");
      }

      num_symbols_imp = PyList_Size(cur_state_obj);

      if (num_symbols_imp != num_symbols)
      {
        return Py_BuildValue("(iis)",-1,8,"Number_of_symbols_do_not_match");
      }

      inMachine[iter_state].t = (TRANSITION *)malloc(num_symbols*sizeof(*(inMachine[iter_state].t)));

      if (inMachine[iter_state].t == NULL)
      {
        return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_machine_state_transition");
      }

      for (iter_symbol = 0; iter_symbol < num_symbols; iter_symbol++)
      {
        PyObject* cur_trans_obj;
        int i0,i1,i2;

        cur_trans_obj = PyList_GetItem(cur_state_obj,iter_symbol);

        if (!PyTuple_CheckExact(cur_trans_obj))
        {
          return Py_BuildValue("(iis)",-1,10,"Unable_to_extract_Turing_machine_transition_3-tuple");
        }

        if (PyTuple_Size(cur_trans_obj) != 3)
        {
          return Py_BuildValue("(iis)",-1,11,"Turing_machine_transition_was_not_a_3-tuple");
        }

        if (!PyArg_ParseTuple(cur_trans_obj,"iii",&i0,&i1,&i2))
        {
          return Py_BuildValue("(iis)",-1,12,"Unable_to_parse_Turing_machine_transition 3-tuple");
        }

        if (i0 < -1 || i0 >= num_symbols)
        {
          return Py_BuildValue("(iis)",-1,13,"Illegal_symbol_in_Turing_machine_transistion_3-tuple");
        }

        if (i1 < 0 || i1 > 1)
        {
          return Py_BuildValue("(iis)",-1,14,"Illegal_direction_in_Turing_machine_transistion_3-tuple");
        }

        if (i2 < -1 || i2 >= num_states)
        {
          return Py_BuildValue("(iis)",-1,15,"Illegal_state_in_Turing_machine_transistion_3-tuple");
        }

        inMachine[iter_state].t[iter_symbol].w = i0;
        inMachine[iter_state].t[iter_symbol].d = 2*i1-1;
        inMachine[iter_state].t[iter_symbol].s = i2;
      }
    }
  }
  
  inTM.num_states  = num_states;
  inTM.num_symbols = num_symbols;

  inTM.machine = inMachine;

  tape_length_obj = PyTuple_GetItem(args,4);

  if (tape_length_obj == NULL || !PyInt_CheckExact(tape_length_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  macroTM.tape_length = PyInt_AsLong(tape_length_obj);
  macroTM.tape = (int *)calloc(macroTM.tape_length,sizeof(*(macroTM.tape)));

  inTM.tape_length = 2*(macro_size+2)+1;
  inTM.tape = (int *)calloc(inTM.tape_length,sizeof(*(inTM.tape)));
  
  macroTM.num_states = num_states;
  macroTM.num_symbols = pow(num_symbols,2*macro_size+1);

  if (inTM.tape == NULL || macroTM.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_tape");
  }

  max_steps_obj = PyTuple_GetItem(args,5);

  if (max_steps_obj == NULL || !PyFloat_CheckExact(max_steps_obj))
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  max_steps = PyFloat_AsDouble(max_steps_obj);

  macroMachine = (MACRO_STATE *)malloc(macroTM.num_states*sizeof(*macroMachine));

  if (macroMachine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_machine");
  }

  for (state = 0; state < inTM.num_states; state++)
  {
    macroMachine[state].t = (MACRO_TRANSITION **)calloc(PRIME_HASH_NUMBER,sizeof(*(macroMachine[state].t)));

    if (macroMachine[state].t == NULL)
    {
      return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_machine_state_transition");
    }
  }

  macroTM.symbol     = (int *)malloc((2*macro_size+1)*sizeof(*(macroTM.symbol)));
  macroTM.new_symbol = (int *)malloc((2*macro_size+1)*sizeof(*(macroTM.new_symbol)));

  macroTM.machine = macroMachine;

  macroTM.max_left  = (macroTM.tape_length-1) / 2;
  macroTM.max_right = (macroTM.tape_length-1) / 2;
  macroTM.position  = (macroTM.tape_length-1) / 2;

  get_macro_symbol(macroTM.symbol,macroTM.tape,macroTM.position,macro_size);
  macroTM.state  = 0;

  macroTM.total_symbols = 0;
  macroTM.total_steps   = 0;

  for (i = 0; i < max_steps; i += (macro_size+1))
  {
    result = step_macro_TM(&macroTM,&inTM);

    if (result != RESULT_STEPPED)
    {
      break;
    }
  }

  if (inMachine != NULL)
  {
    int s;
    for (s = 0; s < inTM.num_states; s++)
    {
      free(inMachine[s].t);
    }

    free(inMachine);
    inMachine = NULL;
  }

  if (inTM.tape != NULL)
  {
    free(inTM.tape);
    inTM.tape = NULL;
  }

  if (macroMachine != NULL)
  {
    int s,i;

    for (s = 0; s < macroTM.num_states; s++)
    {
      for (i = 0; i < PRIME_HASH_NUMBER; i++)
      {
        MACRO_TRANSITION* t;
        MACRO_TRANSITION* nt;

        t = macroMachine[s].t[i];

        while (t != NULL)
        {
          nt = t->next;

          free(t->symbol);
          free(t->w);
          free(t);

          t = nt;
        }
      }

      free(macroMachine[s].t);
    }

    free(macroMachine);
    macroMachine = NULL;
  }

  if (macroTM.tape != NULL)
  {
    free(macroTM.tape);
    macroTM.tape = NULL;
  }

  if (macroTM.symbol != NULL)
  {
    free(macroTM.symbol);
    macroTM.symbol = NULL;
  }

  if (macroTM.new_symbol != NULL)
  {
    free(macroTM.new_symbol);
    macroTM.new_symbol = NULL;
  }

  d_total_symbols = macroTM.total_symbols;
  d_total_steps   = macroTM.total_steps;

  switch (result & RESULT_VALUE)
  {
    case RESULT_HALTED:
      return Py_BuildValue("(idd)",0,d_total_symbols,d_total_steps);
      break;

    case RESULT_NOTAPE:
      return Py_BuildValue("(idd)",1,d_total_symbols,d_total_steps);
      break;

    case RESULT_STEPPED:
      return Py_BuildValue("(idd)",2,d_total_symbols,d_total_steps);
      break;

    case RESULT_UNDEFINED:
      return Py_BuildValue("(iiiidd)",3,
                                      macroTM.state,macroTM.symbol,macroTM.symbol,
                                      d_total_symbols,d_total_steps-1);
      break;

    case RESULT_INFINITE_LEFT:
      return Py_BuildValue("(iis)",4,0,"Infinite_left");
      break;

    case RESULT_INFINITE_RIGHT:
      return Py_BuildValue("(iis)",4,0,"Infinite_right");
      break;
  }

  return Py_BuildValue("(iis)",-1,20,"Reached_the_end_which_is_impossible,_;-)");
}
