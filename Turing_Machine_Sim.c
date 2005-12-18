#include <Python.h>

#include "Turing_Machine.h"

static PyObject* Turing_Machine_Sim_run(PyObject* self,
                                        PyObject* args);

static PyMethodDef Turing_Machine_Sim_Methods[] =
{
  { "run", Turing_Machine_Sim_run, METH_VARARGS, "Run Turing machine" },
  { NULL , NULL                  , 0           , NULL                 }
};

PyMODINIT_FUNC initTuring_Machine_Sim(void)
{
  (void)Py_InitModule("Turing_Machine_Sim",Turing_Machine_Sim_Methods);
}

static PyObject* Turing_Machine_Sim_run(PyObject* self,
                                        PyObject* args)
{
  int symbol;
  int state;
  int new_symbol;
  int new_delta;
  int new_state;

  int                num_syms  = 0;
  unsigned long long num_steps = 0;

  double d_num_syms;
  double d_num_steps;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;
  STATE* machine = NULL;

  PyObject* num_states_obj;
  int num_states,num_states_imp;
  PyObject* num_symbols_obj;
  int num_symbols,num_symbols_imp;

  PyObject* tape_length_obj;
  int tape_length;
  int tape_start = 0;
  int tape_end   = 0;
  int tape_middle;
  int tape_position;
  int *tape = NULL;

  PyObject* max_steps_obj;
  unsigned long long max_steps;

  int infinite;

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
    return Py_BuildValue("(iis)",-1,5,"Number_of_states_don't_match");
  }

  machine = (STATE *)malloc(num_states*sizeof(*machine));

  if (machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_'machine'");
  }

  for (state = 0; state < num_states; state++)
  {
    PyObject* cur_state_obj;
    int cur_symbol;

    cur_state_obj = PyList_GetItem(machine_obj,state);
    if (!PyList_Check(cur_state_obj))
    {
      return Py_BuildValue("(iis)",-1,7,"Unable_to_extract_Turing_machine_transition");
    }

    num_symbols_imp = PyList_Size(cur_state_obj);

    if (num_symbols_imp != num_symbols)
    {
      return Py_BuildValue("(iis)",-1,8,"Number_of_symbols_don't_match");
    }

    machine[state].t = (TRANSITION *)malloc(num_symbols*sizeof(*(machine[state].t)));
    if (machine[state].t == NULL)
    {
      return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_'machine'_state_transition");
    }

    for (cur_symbol = 0; cur_symbol < num_symbols; cur_symbol++)
    {
      PyObject* cur_trans_obj;
      int i0,i1,i2;

      cur_trans_obj = PyList_GetItem(cur_state_obj,cur_symbol);

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

      machine[state].t[cur_symbol].w = i0;
      machine[state].t[cur_symbol].d = 2*i1 - 1;
      machine[state].t[cur_symbol].s = i2;
    }
  }

  tape_length_obj = PyTuple_GetItem(args,3);

  if (tape_length_obj == NULL || !PyInt_CheckExact(tape_length_obj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  tape_length = PyInt_AsLong(tape_length_obj);
  tape_middle = tape_length / 2;

  tape = (int *)calloc(tape_length,sizeof(*tape));

  if (tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_'tape'");
  }

  tape_start    = tape_middle;
  tape_end      = tape_middle;
  tape_position = tape_middle;

  max_steps_obj = PyTuple_GetItem(args,4);

  if (max_steps_obj == NULL || !PyFloat_CheckExact(max_steps_obj))
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  max_steps = PyFloat_AsDouble(max_steps_obj);

  state  = 0;
  symbol = tape[tape_position];

  new_state  = -1;
  new_symbol = -1;

  num_syms  = 0;
  num_steps = 0;

  infinite = 0;
  new_delta = 0;

  for (i = 0; i < max_steps; i++)
  {
    num_steps++;

    symbol = tape[tape_position];

    new_symbol = machine[state].t[symbol].w;
    new_delta  = machine[state].t[symbol].d;
    new_state  = machine[state].t[symbol].s;

    if (new_symbol < 0)
    {
      break;
    }

    if (symbol == 0 && new_symbol != 0)
    {
      num_syms++;
    }

    if (symbol != 0 && new_symbol == 0)
    {
      num_syms--;
    }

    tape[tape_position] = new_symbol;
    tape_position += new_delta;

    if (new_state == -1)
    {
      break;
    }

    if (tape_position < 1 || tape_position >= tape_length-1)
    {
      break;
    }

    if (tape_position < tape_start)
    {
      tape_start = tape_position;

      if (symbol == 0 && new_state == state && new_delta == -1)
      {
        infinite = 1;
        break;
      }
    }

    if (tape_position > tape_end)
    {
      tape_end = tape_position;

      if (symbol == 0 && new_state == state && new_delta == 1)
      {
        infinite = 1;
        break;
      }
    }

    state = new_state;
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

  if (tape != NULL)
  {
    free(tape);
    tape = NULL;
  }

  d_num_syms  = num_syms;
  d_num_steps = num_steps;

  if (infinite == 1)
  {
    if (new_delta == -1)
    {
      return Py_BuildValue("(iis)",4,0,"Infinite_left");
    }
    else
    {
      return Py_BuildValue("(iis)",4,1,"Infinite_right");
    }
  }

  if (new_state == -1)
  {
    if (new_symbol >= 0)
    {
      return Py_BuildValue("(idd)",0,d_num_syms,d_num_steps);
    }
    else
    {
      return Py_BuildValue("(iiiidd)",3,state,symbol,symbol,
                                        d_num_syms,d_num_steps-1);
    }
  }

  if (i < max_steps)
  {
    return Py_BuildValue("(idd)",1,d_num_syms,d_num_steps);
  }
  else
  {
    return Py_BuildValue("(idd)",2,d_num_syms,d_num_steps);
  }

  return Py_BuildValue("(iis)",-1,19,"Reached_the_end_which_is_impossible,_;-)");
}
