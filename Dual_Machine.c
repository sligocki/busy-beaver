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

static PyObject* Dual_Machine_Run(PyObject* self,
                                  PyObject* args);

static PyMethodDef Dual_Machine_Methods[] =
{
  { "run", Dual_Machine_Run, METH_VARARGS, "Run Turing machine" },
  { NULL , NULL            , 0           , NULL                 }
};

PyMODINIT_FUNC initDual_Machine(void)
{
  (void)Py_InitModule("Dual_Machine",Dual_Machine_Methods);
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

static PyObject* Dual_Machine_Run(PyObject* self,
                                  PyObject* args)
{
  TM m1;
  TM m2;

  int result;

  double d_total_symbols;
  double d_total_steps;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;
  STATE* machine = NULL;

  PyObject* num_states_obj;
  int num_states,num_states_imp;

  PyObject* num_symbols_obj;
  int num_symbols,num_symbols_imp;

  PyObject* tape_length_obj;
  int tape_middle;

  PyObject* max_steps_obj;
  unsigned long long max_steps;

  if (!PyTuple_CheckExact(args))
  {
    return Py_BuildValue("(iis)",-1,0,"Argument_was_not_a_tuple");
  }

  n_tuple = PyTuple_Size(args);

  if (n_tuple != 5)
  {
    return Py_BuildValue("(iis)",-1,1,"Expected_a_5-tuple_argument");
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

  machine = (STATE *)malloc(num_states*sizeof(*machine));

  if (machine == NULL)
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

      machine[iter_state].t = (TRANSITION *)malloc(num_symbols*sizeof(*(machine[iter_state].t)));
      if (machine[iter_state].t == NULL)
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

        machine[iter_state].t[iter_symbol].w = i0;
        machine[iter_state].t[iter_symbol].d = 2*i1 - 1;
        machine[iter_state].t[iter_symbol].s = i2;
      }
    }
  }
  
  m1.machine = machine;
  m2.machine = machine;

  tape_length_obj = PyTuple_GetItem(args,3);

  if (tape_length_obj == NULL || !PyInt_CheckExact(tape_length_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  m1.tape_length = PyInt_AsLong(tape_length_obj);
  m2.tape_length = m1.tape_length;

  tape_middle = m1.tape_length / 2;

  m1.tape = (int *)calloc(m1.tape_length,sizeof(*(m1.tape)));
  m2.tape = (int *)calloc(m2.tape_length,sizeof(*(m2.tape)));

  if (m1.tape == NULL || m2.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_tape");
  }

  max_steps_obj = PyTuple_GetItem(args,4);

  if (max_steps_obj == NULL || !PyFloat_CheckExact(max_steps_obj))
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  max_steps = PyFloat_AsDouble(max_steps_obj);

  m1.max_left  = tape_middle;
  m1.max_right = tape_middle;
  m1.position  = tape_middle;

  m1.symbol = m1.tape[m1.position];
  m1.state  = 0;

  m1.total_symbols = 0;
  m1.total_steps   = 0;

  m2.max_left  = tape_middle;
  m2.max_right = tape_middle;
  m2.position  = tape_middle;

  m2.symbol = m2.tape[m2.position];
  m2.state  = 0;

  m2.total_symbols = 0;
  m2.total_steps   = 0;

  for (i = 0; i < max_steps; i += 2)
  {
    result = step_TM(&m1);
      
    if (result != RESULT_STEPPED)
    {
      result |= RESULT_M1;
      break;
    }

    result = step_TM(&m1);
      
    if (result != RESULT_STEPPED)
    {
      result |= RESULT_M1;
      break;
    }

    result = step_TM(&m2);
      
    if (result != RESULT_STEPPED)
    {
      result |= RESULT_M2;
      break;
    }

    if (m1.state == m2.state && m1.symbol == m2.symbol)
    {
      while (m1.tape[m1.max_left] == 0 && m1.max_left < m1.position)
      {
        m1.max_left++;
      }

      while (m2.tape[m2.max_left] == 0 && m2.max_left < m2.position)
      {
        m2.max_left++;
      }

      if (m1.position - m1.max_left == m2.position - m2.max_left)
      {
        while (m1.tape[m1.max_right] == 0 && m1.max_right > m1.position)
        {
          m1.max_right--;
        }

        while (m2.tape[m2.max_right] == 0 && m2.max_right > m2.position)
        {
          m2.max_right--;
        }

        if (m1.max_right - m1.position == m2.max_right - m2.position)
        {
          int p1,p2;

          for (p1 = m1.max_left, p2 = m2.max_left;
               p1 <= m1.max_right && p2 <= m2.max_right;
               p1++, p2++)
          {
            if (m1.tape[p1] != m2.tape[p2])
            {
              break;
            }
          }

          if (m1.tape[p1] == m2.tape[p2])
          {
            result = RESULT_INFINITE_DUAL | RESULT_BOTH;
            break;
          }
        }
      }
    }
  }

  if (machine != NULL)
  {
    int s;
    for (s = 0; s < num_states; s++)
    {
      free(machine[s].t);
    }

    free(machine);
    machine = NULL;
  }

  if (m1.tape != NULL)
  {
    free(m1.tape);
    m1.tape = NULL;
  }

  if (m2.tape != NULL)
  {
    free(m2.tape);
    m2.tape = NULL;
  }

  if ((result & RESULT_VALUE) == RESULT_INFINITE_DUAL)
  {
    return Py_BuildValue("(iis)",4,2,"Infinite_dual_run");
  }
  else
  {
    if ((result & RESULT_MACHINE) == RESULT_M1)
    {
      d_total_symbols = m1.total_symbols;
      d_total_steps   = m1.total_steps;

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
          return Py_BuildValue("(iiiidd)",3,m1.state,m1.symbol,m1.symbol,
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
      d_total_symbols = m2.total_symbols;
      d_total_steps   = m2.total_steps;

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
          return Py_BuildValue("(iiiidd)",3,m2.state,m2.symbol,m2.symbol,
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
