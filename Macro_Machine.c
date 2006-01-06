#include <Python.h>

#include "Turing_Machine.h"
#include "Macro_Machine.h"

static PyObject* Macro_Machine(PyObject* self,
                               PyObject* args);

static PyMethodDef Macro_Machine_Methods[] =
{
  { "Macro_Machine", Macro_Machine, METH_VARARGS, "Run Turing machine" },
  { NULL           , NULL         , 0           , NULL                 }
};

PyMODINIT_FUNC initMacro_Machine(void)
{
  (void)Py_InitModule("Macro_Machine",Macro_Machine_Methods);
}

inline void get_macro_symbol(int* symbol, int* tape, int position, int size)
{
  int i;
  for (i = 0; i < 2*size-1; i++)
  {
    symbol[i] = tape[i-size+1 + position];
    if (symbol[i] < 0 || symbol[i] > 10)
    {
      fprintf(stderr,"--- Getting bad data: %d %d %d, %d...\n",i,size,position,i-size+1 + position);
      abort();
    }
  }
}

inline void put_macro_symbol(int* symbol, int* tape, int position, int size)
{
  int i;
  for (i = 0; i < 2*size-1; i++)
  {
    if (symbol[i] < 0 || symbol[i] > 10)
    {
      fprintf(stderr,"--- Putting bad data: %d %d %d, %d...\n",i,size,position,i-size+1 + position);
      abort();
    }
    tape[i-size+1 + position] = symbol[i];
  }
}

inline int equal_symbol(int* symbol1, int* symbol2, int size)
{
  int i;
  int equal = 1;

  for (i = 0; i < 2*size-1; i++)
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
  for (i = 0; i < 2*m->size-1; i++)
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

inline MACRO_TRANSITION* hash_add(MACRO_TM* m, int state, int* symbol, TM* baseTM, PyObject** error_value)
{
  int i;
  int hash_index;
  MACRO_TRANSITION* trans;

  int start;
  int step;

  int result;

  *error_value = NULL;

  hash_index = 0;
  for (i = 0; i < 2*m->size-1; i++)
  {
    hash_index = (hash_index*baseTM->num_symbols + symbol[i]) % PRIME_HASH_NUMBER;
  }

  trans = (MACRO_TRANSITION *)malloc(sizeof(*trans));

  trans->symbol = (int *)malloc((2*m->size-1) * sizeof(*(trans->symbol)));
  for (i = 0; i < 2*m->size-1; i++)
  {
    trans->symbol[i] = symbol[i];
  }

  trans->w = (int *)malloc((2*m->size-1) * sizeof(*(trans->w)));

  trans->next = m->machine[state].t[hash_index];
  m->machine[state].t[hash_index] = trans;

  baseTM->tape[0                    ] = 0;
  baseTM->tape[1                    ] = 0;
  baseTM->tape[baseTM->tape_length-2] = 0;
  baseTM->tape[baseTM->tape_length-1] = 0;

  baseTM->position = (baseTM->tape_length-1) / 2;
  put_macro_symbol(symbol,baseTM->tape,baseTM->position,m->size);

  baseTM->max_left  = (baseTM->tape_length-1) / 2;
  baseTM->max_right = (baseTM->tape_length-1) / 2;

  baseTM->total_symbols = 0;
  baseTM->total_steps   = 0;

  baseTM->state  = state;
  baseTM->symbol = baseTM->tape[baseTM->position];

  start = baseTM->position;

  result = RESULT_INVALID;

  for (step = 0; step < m->size; step++)
  {
    result = step_TM(baseTM);

    if (result != RESULT_STEPPED)
    {
      break;
    }
  }

  switch (result & RESULT_VALUE)
  {
    case RESULT_HALTED:
      free(trans->w);
      free(trans);
      trans = NULL;

      *error_value = Py_BuildValue("(iNN)",
                       0,
                       PyLong_FromUnsignedLongLong(m->total_symbols),
                       PyLong_FromUnsignedLongLong(m->total_steps + step));
      break;

    case RESULT_NOTAPE:
      free(trans->w);
      free(trans);
      trans = NULL;

      *error_value = Py_BuildValue("(iis)",-1,26,"Ran_out_of_tape");
      break;

    case RESULT_STEPPED:
      get_macro_symbol(trans->w, baseTM->tape, start, m->size);
      trans->d = baseTM->position-start;
      trans->s = baseTM->state;

      *error_value = NULL;
      break;

    case RESULT_UNDEFINED:
      free(trans->w);
      free(trans);
      trans = NULL;

      *error_value = Py_BuildValue("(iiiNN)",3,
                       3,baseTM->state,baseTM->symbol,
                       PyLong_FromUnsignedLongLong(m->total_symbols),
                       PyLong_FromUnsignedLongLong(m->total_steps + step));
      break;

    default:
      free(trans->w);
      free(trans);
      trans = NULL;

      *error_value = Py_BuildValue("(iis)",-1,27,"Unexpected_result_for_Turing_machine");
      break;
  }

  return trans;
}

inline int step_macro_TM(MACRO_TM* m, TM* baseTM, PyObject** error_value)
{
  int i;
  MACRO_TRANSITION* trans;

  trans = hash_lookup(m,m->state,m->symbol,baseTM->num_symbols);

  if (trans == NULL)
  {
    *error_value = NULL;
    trans = hash_add(m,m->state,m->symbol,baseTM,error_value);
  }

  if (trans == NULL)
  {
    return RESULT_INVALID;
  }

  for (i = 0; i < 2*m->size-1; i++)
  {
    m->new_symbol[i] = trans->w[i];
  }

  m->new_delta  = trans->d;
  m->new_state  = trans->s;

  if (m->new_symbol[0] == -1)
  {
    return RESULT_UNDEFINED;
  }

  m->total_steps += m->size;

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

  for (i = 0; i < 2*m->size-1; i++)
  {
    m->symbol[i] = m->new_symbol[i];
  }

  m->state = m->new_state;

  return RESULT_STEPPED;
}

inline void free_macro_TM(MACRO_TM* m)
{
  if (m != NULL)
  {
    if (m->machine != NULL)
    {
      int s,i;

      for (s = 0; s < m->num_states; s++)
      {
        for (i = 0; i < PRIME_HASH_NUMBER; i++)
        {
          MACRO_TRANSITION* t;
          MACRO_TRANSITION* nt;

          t = m->machine[s].t[i];

          while (t != NULL)
          {
            nt = t->next;

            free(t->symbol);
            free(t->w);
            free(t);

            t = nt;
          }
        }

        free(m->machine[s].t);
      }

      free(m->machine);
      m->machine = NULL;
    }

    if (m->tape != NULL)
    {
      free(m->tape);
      m->tape = NULL;
    }

    if (m->symbol != NULL)
    {
      free(m->symbol);
      m->symbol = NULL;
    }

    if (m->new_symbol != NULL)
    {
      free(m->new_symbol);
      m->new_symbol = NULL;
    }
  }
}

static PyObject* Macro_Machine(PyObject* self,
                               PyObject* args)
{
  TM inTM;
  MACRO_TM macroTM;

  int result;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;

  PyObject* num_states_obj;
  int num_states_imp;

  PyObject* num_symbols_obj;
  int num_symbols_imp;

  PyObject* tape_length_obj;

  PyObject* macro_size_obj;

  PyObject* max_steps_obj;
  unsigned long long max_steps;

  PyObject* error_value;

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

  inTM.num_states = PyInt_AsLong(num_states_obj);

  num_symbols_obj = PyTuple_GetItem(args,2);
  if (num_symbols_obj == NULL || !PyInt_CheckExact(num_symbols_obj))
  {
    return Py_BuildValue("(iis)",-1,4,"Unable_to_extract_#_of_symbols");
  }

  inTM.num_symbols = PyInt_AsLong(num_symbols_obj);

  macro_size_obj = PyTuple_GetItem(args,3);

  if (macro_size_obj == NULL || !PyInt_CheckExact(macro_size_obj))
  {
    return Py_BuildValue("(iis)",-1,5,"Unable_to_extract_macro_size");
  }

  macroTM.size = PyInt_AsLong(macro_size_obj);

  if (macroTM.size < 1)
  {
    return Py_BuildValue("(iis)",-1,6,"Macro_size_must_be_greater_than_zero");
  }

  num_states_imp = PyList_Size(machine_obj);

  if (num_states_imp != inTM.num_states)
  {
    return Py_BuildValue("(iis)",-1,7,"Number_of_states_do_not_match");
  }

  inTM.machine = (STATE *)malloc(inTM.num_states*sizeof(*inTM.machine));

  if (inTM.machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,8,"Out_of_memory_allocating_machine");
  }

  {
    int iter_state;
    for (iter_state = 0; iter_state < inTM.num_states; iter_state++)
    {
      int iter_symbol;
      PyObject* cur_state_obj;

      cur_state_obj = PyList_GetItem(machine_obj,iter_state);
      if (!PyList_Check(cur_state_obj))
      {
        return Py_BuildValue("(iis)",-1,9,"Unable_to_extract_Turing_machine_transition");
      }

      num_symbols_imp = PyList_Size(cur_state_obj);

      if (num_symbols_imp != inTM.num_symbols)
      {
        return Py_BuildValue("(iis)",-1,10,"Number_of_symbols_do_not_match");
      }

      inTM.machine[iter_state].t = (TRANSITION *)malloc(inTM.num_symbols*sizeof(*(inTM.machine[iter_state].t)));

      if (inTM.machine[iter_state].t == NULL)
      {
        return Py_BuildValue("(iis)",-1,11,"Out_of_memory_allocating_machine_state_transition");
      }

      for (iter_symbol = 0; iter_symbol < inTM.num_symbols; iter_symbol++)
      {
        PyObject* cur_trans_obj;
        int i0,i1,i2;

        cur_trans_obj = PyList_GetItem(cur_state_obj,iter_symbol);

        if (!PyTuple_CheckExact(cur_trans_obj))
        {
          return Py_BuildValue("(iis)",-1,12,"Unable_to_extract_Turing_machine_transition_3-tuple");
        }

        if (PyTuple_Size(cur_trans_obj) != 3)
        {
          return Py_BuildValue("(iis)",-1,13,"Turing_machine_transition_was_not_a_3-tuple");
        }

        if (!PyArg_ParseTuple(cur_trans_obj,"iii",&i0,&i1,&i2))
        {
          return Py_BuildValue("(iis)",-1,14,"Unable_to_parse_Turing_machine_transition 3-tuple");
        }

        if (i0 < -1 || i0 >= inTM.num_symbols)
        {
          return Py_BuildValue("(iis)",-1,15,"Illegal_symbol_in_Turing_machine_transistion_3-tuple");
        }

        if (i1 < 0 || i1 > 1)
        {
          return Py_BuildValue("(iis)",-1,16,"Illegal_direction_in_Turing_machine_transistion_3-tuple");
        }

        if (i2 < -1 || i2 >= inTM.num_states)
        {
          return Py_BuildValue("(iis)",-1,17,"Illegal_state_in_Turing_machine_transistion_3-tuple");
        }

        inTM.machine[iter_state].t[iter_symbol].w = i0;
        inTM.machine[iter_state].t[iter_symbol].d = 2*i1-1;
        inTM.machine[iter_state].t[iter_symbol].s = i2;
      }
    }
  }
  
  tape_length_obj = PyTuple_GetItem(args,4);

  if (tape_length_obj == NULL)
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_tape_length");
  }

  if (PyInt_CheckExact(tape_length_obj))
  {
    macroTM.tape_length = PyInt_AsLong(tape_length_obj);
  }
  else
  if (PyLong_CheckExact(tape_length_obj))
  {
    macroTM.tape_length = PyLong_AsUnsignedLongLong(tape_length_obj);
  }
  else
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_tape_length");
  }

  macroTM.tape = (int *)calloc(macroTM.tape_length,sizeof(*(macroTM.tape)));

  inTM.tape_length = 2*(macroTM.size+1)+1;
  inTM.tape = (int *)calloc(inTM.tape_length,sizeof(*(inTM.tape)));
  
  macroTM.num_states  = inTM.num_states;
  macroTM.num_symbols = pow(inTM.num_symbols,2*macroTM.size-1);

  if (inTM.tape == NULL || macroTM.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,19,"Out_of_memory_allocating_tape");
  }

  max_steps_obj = PyTuple_GetItem(args,5);

  if (max_steps_obj == NULL)
  {
    return Py_BuildValue("(iis)",-1,20,"Unable_to_extract_maximum_#_of_steps");
  }

  if (PyInt_CheckExact(max_steps_obj))
  {
    max_steps = PyInt_AsLong(max_steps_obj);
  }
  else
  if (PyLong_CheckExact(max_steps_obj))
  {
    max_steps = PyLong_AsUnsignedLongLong(max_steps_obj);
  }
  else
  {
    return Py_BuildValue("(iis)",-1,20,"Unable_to_extract_maximum_#_of_steps");
  }

  macroTM.machine = (MACRO_STATE *)malloc(macroTM.num_states*sizeof(*macroTM.machine));

  if (macroTM.machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,21,"Out_of_memory_allocating_machine");
  }

  for (state = 0; state < inTM.num_states; state++)
  {
    macroTM.machine[state].t = (MACRO_TRANSITION **)calloc(PRIME_HASH_NUMBER,sizeof(*(macroTM.machine[state].t)));

    if (macroTM.machine[state].t == NULL)
    {
      return Py_BuildValue("(iis)",-1,22,"Out_of_memory_allocating_machine_state_transition");
    }
  }

  macroTM.symbol     = (int *)malloc((2*macroTM.size-1)*sizeof(*(macroTM.symbol)));
  macroTM.new_symbol = (int *)malloc((2*macroTM.size-1)*sizeof(*(macroTM.new_symbol)));

  macroTM.max_left  = (macroTM.tape_length-1) / 2;
  macroTM.max_right = (macroTM.tape_length-1) / 2;
  macroTM.position  = (macroTM.tape_length-1) / 2;

  get_macro_symbol(macroTM.symbol,macroTM.tape,macroTM.position,macroTM.size);
  macroTM.state  = 0;

  macroTM.total_symbols = -1;
  macroTM.total_steps   =  0;

  result = RESULT_INVALID;
  error_value = NULL;

  for (i = 0; i < max_steps; i += macroTM.size)
  {
    result = step_macro_TM(&macroTM,&inTM,&error_value);

    if (result != RESULT_STEPPED)
    {
      break;
    }
  }

  free_TM(&inTM);
  free_macro_TM(&macroTM);

  switch (result & RESULT_VALUE)
  {
    case RESULT_NOTAPE:
      return Py_BuildValue("(iNN)",
                           1,
                           PyLong_FromUnsignedLongLong(macroTM.total_symbols),
                           PyLong_FromUnsignedLongLong(macroTM.total_steps));
      break;

    case RESULT_STEPPED:
      return Py_BuildValue("(iNN)",
                           2,
                           PyLong_FromUnsignedLongLong(macroTM.total_symbols),
                           PyLong_FromUnsignedLongLong(macroTM.total_steps));
      break;


    case RESULT_INFINITE_LEFT:
      return Py_BuildValue("(iiis)",4,0,macroTM.size,"Macro_infinite_left");
      break;

    case RESULT_INFINITE_RIGHT:
      return Py_BuildValue("(iiis)",4,1,macroTM.size,"Macro_infinite_right");
      break;

    case RESULT_INVALID:
      if (error_value == NULL)
      {
        return Py_BuildValue("(iis)",-1,23,"Unexpected_result_for_Turing_machine");
      }
      else
      {
        return error_value;
      }
      break;

    default:
      return Py_BuildValue("(iis)",-1,24,"Unexpected_result_for_Turing_machine");
      break;
  }

  return Py_BuildValue("(iis)",-1,25,"Reached_the_end_which_is_impossible,_;-)");
}
