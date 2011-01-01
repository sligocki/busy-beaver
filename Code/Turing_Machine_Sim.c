#include <Python.h>

#include "Turing_Machine.h"

static PyObject* Turing_Machine_Sim(PyObject* self,
                                    PyObject* args);

static PyMethodDef Turing_Machine_Sim_Methods[] =
{
  { "Turing_Machine_Sim", Turing_Machine_Sim, METH_VARARGS, "Run Turing machine" },
  { NULL                , NULL              , 0           , NULL                 }
};

PyMODINIT_FUNC initTuring_Machine_Sim(void)
{
  (void)Py_InitModule("Turing_Machine_Sim",Turing_Machine_Sim_Methods);
}

static PyObject* Turing_Machine_Sim(PyObject* self,
                                    PyObject* args)
{
  TM tm;

  int result;

  unsigned long long i;
  int n_tuple;

  PyObject* machine_obj;

  PyObject* num_states_obj;
  int num_states_imp;

  PyObject* num_symbols_obj;
  int num_symbols_imp;

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

  tm.num_states = PyInt_AsLong(num_states_obj);

  num_symbols_obj = PyTuple_GetItem(args,2);
  if (num_symbols_obj == NULL || !PyInt_CheckExact(num_symbols_obj))
  {
    return Py_BuildValue("(iis)",-1,4,"Unable_to_extract_#_of_symbols");
  }

  tm.num_symbols = PyInt_AsLong(num_symbols_obj);

  num_states_imp = PyList_Size(machine_obj);

  if (num_states_imp != tm.num_states)
  {
    return Py_BuildValue("(iis)",-1,5,"Number_of_states_don't_match");
  }

  tm.machine = (STATE *)malloc(tm.num_states*sizeof(*tm.machine));

  if (tm.machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_'machine'");
  }

  {
    int iter_state;
    for (iter_state = 0; iter_state < tm.num_states; iter_state++)
    {
      int iter_symbol;
      PyObject* cur_state_obj;

      cur_state_obj = PyList_GetItem(machine_obj,iter_state);
      if (!PyList_Check(cur_state_obj))
      {
        return Py_BuildValue("(iis)",-1,7,"Unable_to_extract_Turing_machine_transition");
      }

      num_symbols_imp = PyList_Size(cur_state_obj);

      if (num_symbols_imp != tm.num_symbols)
      {
        return Py_BuildValue("(iis)",-1,8,"Number_of_symbols_don't_match");
      }

      tm.machine[iter_state].t = (TRANSITION *)malloc(tm.num_symbols*sizeof(*(tm.machine[iter_state].t)));
      if (tm.machine[iter_state].t == NULL)
      {
        return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_'machine'_state_transition");
      }

      for (iter_symbol = 0; iter_symbol < tm.num_symbols; iter_symbol++)
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

        if (i0 < -1 || i0 >= tm.num_symbols)
        {
          return Py_BuildValue("(iis)",-1,13,"Illegal_symbol_in_Turing_machine_transistion_3-tuple");
        }

        if (i1 < 0 || i1 > 1)
        {
          return Py_BuildValue("(iis)",-1,14,"Illegal_direction_in_Turing_machine_transistion_3-tuple");
        }

        if (i2 < -1 || i2 >= tm.num_states)
        {
          return Py_BuildValue("(iis)",-1,15,"Illegal_state_in_Turing_machine_transistion_3-tuple");
        }

        tm.machine[iter_state].t[iter_symbol].w = i0;
        tm.machine[iter_state].t[iter_symbol].d = 2*i1 - 1;
        tm.machine[iter_state].t[iter_symbol].s = i2;
      }
    }
  }

  tape_length_obj = PyTuple_GetItem(args,3);

  if (tape_length_obj == NULL)
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  if (PyInt_CheckExact(tape_length_obj))
  {
    tm.tape_length = PyInt_AsLong(tape_length_obj);
  }
  else
  if (PyLong_CheckExact(tape_length_obj))
  {
    tm.tape_length = PyLong_AsUnsignedLongLong(tape_length_obj);
  }
  else
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  tape_middle = tm.tape_length / 2;

  tm.tape = (int *)calloc(tm.tape_length,sizeof(*(tm.tape)));

  if (tm.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_'tape'");
  }

  max_steps_obj = PyTuple_GetItem(args,4);

  if (max_steps_obj == NULL)
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
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
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  tm.max_left  = tape_middle;
  tm.max_right = tape_middle;
  tm.position  = tape_middle;

  tm.symbol = tm.tape[tm.position];
  tm.state  = 0;

  tm.total_symbols = 0;
  tm.total_steps   = 0;

  result = RESULT_INVALID;

  for (i = 0; i < max_steps; i++)
  {
    result = step_TM(&tm);

    if (result != RESULT_STEPPED)
    {
      break;
    }
  }

  free_TM(&tm);

  switch (result & RESULT_VALUE)
  {
    case RESULT_HALTED:
      return Py_BuildValue("(iNN)",
                           0,
                           PyLong_FromUnsignedLongLong(tm.total_symbols),
                           PyLong_FromUnsignedLongLong(tm.total_steps));
      break;

    case RESULT_NOTAPE:
      return Py_BuildValue("(iNN)",
                           1,
                           PyLong_FromUnsignedLongLong(tm.total_symbols),
                           PyLong_FromUnsignedLongLong(tm.total_steps));
      break;

    case RESULT_STEPPED:
      return Py_BuildValue("(iNN)",
                           2,
                           PyLong_FromUnsignedLongLong(tm.total_symbols),
                           PyLong_FromUnsignedLongLong(tm.total_steps));
      break;

    case RESULT_UNDEFINED:
      return Py_BuildValue("(iiiNN)",
                           3,tm.state,tm.symbol,
                           PyLong_FromUnsignedLongLong(tm.total_symbols),
                           PyLong_FromUnsignedLongLong(tm.total_steps));
      break;

    default:
      return Py_BuildValue("(iis)",-1,19,"Unexpected_result_for_Turing_machine");
      break;
  }

  return Py_BuildValue("(iis)",-1,20,"Reached_the_end_which_is_impossible,_;-)");
}
