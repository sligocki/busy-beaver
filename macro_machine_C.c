#include <Python.h>

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

static PyObject* macro_machine_C_run(PyObject* self,
                                   PyObject* args);

static PyMethodDef macro_machine_C_methods[] =
{
  { "run", macro_machine_C_run, METH_VARARGS, "Run Turing machine" },
  { NULL , NULL             , 0           , NULL                 }
};

PyMODINIT_FUNC initmacro_machine_C(void)
{
  (void)Py_InitModule("macro_machine_C",macro_machine_C_methods);
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

  if (m->position < 1 || m->position >= m->tape_length - 1)
  {
    return RESULT_NOTAPE;
  }
  
  if (m->position < m->max_left)
  {
    m->max_left = m->position;

    if (m->symbol == 0 && m->new_state == m->state && m->new_delta == -1)
    {
      return RESULT_INFINITE_LEFT;
    }
  }

  if (m->position > m->max_right)
  {
    m->max_right = m->position;

    if (m->symbol == 0 && m->new_state == m->state && m->new_delta == 1)
    {
      return RESULT_INFINITE_RIGHT;
    }
  }

  m->symbol = m->tape[m->position];
  m->state = m->new_state;

  return RESULT_STEPPED;
}

static PyObject* macro_machine_C_run(PyObject* self,
                                     PyObject* args)
{
  TM inTM;
  TM macroTM;

  int result;

  double d_total_symbols;
  double d_total_steps;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;
  STATE* inMachine = NULL;
  STATE* macroMachine = NULL;

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
        inMachine[iter_state].t[iter_symbol].d = 2*i1 - 1;
        inMachine[iter_state].t[iter_symbol].s = i2;
      }
    }
  }
  
  inTM.num_states  = num_states;
  inTM.num_symbols = num_symbols;

  inTM.machine = inMachine;

  tape_length_obj = PyTuple_GetItem(args,3);

  if (tape_length_obj == NULL || !PyInt_CheckExact(tape_length_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  macroTM.tape_length = PyInt_AsLong(tape_length_obj);
  macroTM.tape = (int *)calloc(macroTM.tape_length,sizeof(*(macroTM.tape)));

  macro_size_obj = PyTuple_GetItem(args,3);

  if (macro_size_obj == NULL || !PyInt_CheckExact(macro_size_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_macro_size");
  }

  macro_size = PyInt_AsLong(macro_size_obj);

  inTM.tape_length = 2*(macro_size+1) + 1;
  inTM.tape = (int *)calloc(inTM.tape_length,sizeof(*(inTM.tape)));
  
  macroTM.num_states = num_states;
  macroTM.num_symbols = pow(num_symbols,2*macro_size + 1);

  if (inTM.tape == NULL || macroTM.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_tape");
  }

  max_steps_obj = PyTuple_GetItem(args,4);

  if (max_steps_obj == NULL || !PyFloat_CheckExact(max_steps_obj))
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  max_steps = PyFloat_AsDouble(max_steps_obj);

  macroMachine = (STATE *)malloc(macroTM.num_states*sizeof(*macroMachine));

  if (macroMachine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_machine");
  }

  for (state = 0; state < inTM.num_states; state++)
  {
    int symbol;

    macroMachine[state].t = (TRANSITION *)malloc(macroTM.num_symbols*sizeof(*(macroMachine[state].t)));

    if (macroMachine[state].t == NULL)
    {
      return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_machine_state_transition");
    }

    for (symbol = 0; symbol < macroTM.num_symbols; symbol++)
    {
      int remain_symbol;
      int fill;
      int start;
      int step;
      int out_symbol;

      inTM.tape[0                 ] = 0;
      inTM.tape[inTM.tape_length-1] = 0;

      remain_symbol = symbol;
      for (fill = 1; fill < inTM.tape_length - 1; fill++)
      {
        int in_symbol;

        in_symbol = remain_symbol % num_symbols;
        remain_symbol = remain_symbol / num_symbols;

        inTM.tape[fill] = in_symbol;
      }

      inTM.max_left  = (inTM.tape_length + 1) / 2;
      inTM.max_right = (inTM.tape_length + 1) / 2;
      inTM.position  = (inTM.tape_length + 1) / 2;

      inTM.total_symbols = 0;
      inTM.total_steps   = 0;

      inTM.state  = state;
      inTM.symbol = inTM.tape[inTM.position];

      start = inTM.position;

      for (step = 0; step < macro_size; step++)
      {
        result = step_TM(&inTM);

        if (result != RESULT_STEPPED)
        {
        }
      }

      out_symbol = 0;
      for (fill = inTM.tape_length - 2; fill >= 0; fill--)
      {
        out_symbol = num_symbols*out_symbol | inTM.tape[fill];
      }

      macroMachine[state].t[symbol].w = out_symbol;
      macroMachine[state].t[symbol].d = inTM.position - start;
      macroMachine[state].t[symbol].s = inTM.state;
    }
  }

  macroTM.max_left  = (macroTM.tape_length + 1) / 2;
  macroTM.max_right = (macroTM.tape_length + 1) / 2;
  macroTM.position  = (macroTM.tape_length + 1) / 2;

  macroTM.symbol = macroTM.tape[macroTM.position];
  macroTM.state  = 0;

  macroTM.total_symbols = 0;
  macroTM.total_steps   = 0;

  for (i = 0; i < max_steps; i += 2)
  {
    result = step_TM(&macroTM);
      
    if (result != RESULT_STEPPED)
    {
      result |= RESULT_M2;
      break;
    }

    if (inTM.state == macroTM.state && inTM.symbol == macroTM.symbol)
    {
      while (inTM.tape[inTM.max_left] == 0 && inTM.max_left < inTM.position)
      {
        inTM.max_left++;
      }

      while (macroTM.tape[macroTM.max_left] == 0 && macroTM.max_left < macroTM.position)
      {
        macroTM.max_left++;
      }

      if (inTM.position - inTM.max_left == macroTM.position - macroTM.max_left)
      {
        while (inTM.tape[inTM.max_right] == 0 && inTM.max_right > inTM.position)
        {
          inTM.max_right--;
        }

        while (macroTM.tape[macroTM.max_right] == 0 && macroTM.max_right > macroTM.position)
        {
          macroTM.max_right--;
        }

        if (inTM.max_right - inTM.position == macroTM.max_right - macroTM.position)
        {
          int p1,p2;

          for (p1 = inTM.max_left, p2 = macroTM.max_left;
               p1 <= inTM.max_right && p2 <= macroTM.max_right;
               p1++, p2++)
          {
            if (inTM.tape[p1] != macroTM.tape[p2])
            {
              break;
            }
          }

          if (inTM.tape[p1] == macroTM.tape[p2])
          {
            result = RESULT_INFINITE_DUAL | RESULT_BOTH;
            break;
          }
        }
      }
    }
  }

  if (inMachine != NULL)
  {
    int s;
    for (s = 0; s < num_states; s++)
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

  if (macroTM.tape != NULL)
  {
    free(macroTM.tape);
    macroTM.tape = NULL;
  }

  if ((result & RESULT_VALUE) == RESULT_INFINITE_DUAL)
  {
    return Py_BuildValue("(iis)",4,2,"Infinite_dual_run");
  }
  else
  {
    if ((result & RESULT_MACHINE) == RESULT_M1)
    {
      d_total_symbols = inTM.total_symbols;
      d_total_steps   = inTM.total_steps;

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
          return Py_BuildValue("(iiiidd)",3,inTM.state,inTM.symbol,inTM.symbol,
                                          d_total_symbols,d_total_steps-1);
          break;

        case RESULT_INFINITE_LEFT:
          return Py_BuildValue("(iis)",4,0,"Infinite_left");
          break;

        case RESULT_INFINITE_RIGHT:
          return Py_BuildValue("(iis)",4,0,"Infinite_right");
          break;
      }
    }
    else
    if ((result & RESULT_MACHINE) == RESULT_M2)
    {
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
          return Py_BuildValue("(iiiidd)",3,macroTM.state,macroTM.symbol,macroTM.symbol,
                                          d_total_symbols,d_total_steps-1);
          break;

        case RESULT_INFINITE_LEFT:
          return Py_BuildValue("(iis)",4,0,"Infinite_left");
          break;

        case RESULT_INFINITE_RIGHT:
          return Py_BuildValue("(iis)",4,0,"Infinite_right");
          break;
      }
    }
    else
    {
      return Py_BuildValue("(iis)",-1,19,"Normal_stop_but_not_machine_specific");
    }
  }

  return Py_BuildValue("(iis)",-1,20,"Reached_the_end_which_is_impossible,_;-)");
}
