#include <Python.h>

#include "Turing_Machine.h"

static PyObject* Dual_Machine(PyObject* self,
                              PyObject* args);

static PyMethodDef Dual_Machine_Methods[] =
{
  { "Dual_Machine", Dual_Machine, METH_VARARGS, "Run Turing machine" },
  { NULL          , NULL            , 0           , NULL                 }
};

PyMODINIT_FUNC initDual_Machine(void)
{
  (void)Py_InitModule("Dual_Machine",Dual_Machine_Methods);
}

static PyObject* Dual_Machine(PyObject* self,
                              PyObject* args)
{
  TM m1;
  TM m2;

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

  m1.num_states = PyInt_AsLong(num_states_obj);
  m2.num_states = m1.num_states;

  num_symbols_obj = PyTuple_GetItem(args,2);
  if (num_symbols_obj == NULL || !PyInt_CheckExact(num_symbols_obj))
  {
    return Py_BuildValue("(iis)",-1,4,"Unable_to_extract_#_of_symbols");
  }

  m1.num_symbols = PyInt_AsLong(num_symbols_obj);
  m2.num_symbols = m1.num_symbols;

  num_states_imp = PyList_Size(machine_obj);

  if (num_states_imp != m1.num_states)
  {
    return Py_BuildValue("(iis)",-1,5,"Number_of_states_do_not_match");
  }

  m1.machine = (STATE *)malloc(m1.num_states*sizeof(*m1.machine));
  if (m1.machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_machine");
  }

  m2.machine = (STATE *)malloc(m2.num_states*sizeof(*m2.machine));
  if (m2.machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_machine");
  }

  {
    int iter_state;
    for (iter_state = 0; iter_state < m1.num_states; iter_state++)
    {
      int iter_symbol;
      PyObject* cur_state_obj;

      cur_state_obj = PyList_GetItem(machine_obj,iter_state);
      if (!PyList_Check(cur_state_obj))
      {
        return Py_BuildValue("(iis)",-1,7,"Unable_to_extract_Turing_machine_transition");
      }

      num_symbols_imp = PyList_Size(cur_state_obj);

      if (num_symbols_imp != m1.num_symbols)
      {
        return Py_BuildValue("(iis)",-1,8,"Number_of_symbols_do_not_match");
      }

      m1.machine[iter_state].t = (TRANSITION *)malloc(m1.num_symbols*sizeof(*(m1.machine[iter_state].t)));
      if (m1.machine[iter_state].t == NULL)
      {
        return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_machine_state_transition");
      }

      m2.machine[iter_state].t = (TRANSITION *)malloc(m2.num_symbols*sizeof(*(m2.machine[iter_state].t)));
      if (m2.machine[iter_state].t == NULL)
      {
        return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_machine_state_transition");
      }

      for (iter_symbol = 0; iter_symbol < m1.num_symbols; iter_symbol++)
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

        if (i0 < -1 || i0 >= m1.num_symbols)
        {
          return Py_BuildValue("(iis)",-1,13,"Illegal_symbol_in_Turing_machine_transistion_3-tuple");
        }

        if (i1 < 0 || i1 > 1)
        {
          return Py_BuildValue("(iis)",-1,14,"Illegal_direction_in_Turing_machine_transistion_3-tuple");
        }

        if (i2 < -1 || i2 >= m1.num_states)
        {
          return Py_BuildValue("(iis)",-1,15,"Illegal_state_in_Turing_machine_transistion_3-tuple");
        }

        m1.machine[iter_state].t[iter_symbol].w = i0;
        m1.machine[iter_state].t[iter_symbol].d = 2*i1 - 1;
        m1.machine[iter_state].t[iter_symbol].s = i2;

        m2.machine[iter_state].t[iter_symbol].w = i0;
        m2.machine[iter_state].t[iter_symbol].d = 2*i1 - 1;
        m2.machine[iter_state].t[iter_symbol].s = i2;
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
    m1.tape_length = PyInt_AsLong(tape_length_obj);
  }
  else
  if (PyLong_CheckExact(tape_length_obj))
  {
    m1.tape_length = PyLong_AsUnsignedLongLong(tape_length_obj);
  }
  else
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  m2.tape_length = m1.tape_length;

  tape_middle = m1.tape_length / 2;

  m1.tape = (int *)calloc(m1.tape_length,sizeof(*(m1.tape)));
  m2.tape = (int *)calloc(m2.tape_length,sizeof(*(m2.tape)));

  if (m1.tape == NULL || m2.tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_tape");
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

  result = RESULT_INVALID;

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

  free_TM(&m1);
  free_TM(&m2);

  if ((result & RESULT_VALUE) == RESULT_INFINITE_DUAL)
  {
    return Py_BuildValue("(iis)",4,2,"Infinite_dual_run");
  }
  else
  {
    if ((result & RESULT_MACHINE) == RESULT_M1)
    {
      switch (result & RESULT_VALUE)
      {
        case RESULT_HALTED:
          return Py_BuildValue("(iNN)",
                               0,
                               PyLong_FromUnsignedLongLong(m1.total_symbols),
                               PyLong_FromUnsignedLongLong(m1.total_steps));
          break;

        case RESULT_NOTAPE:
          return Py_BuildValue("(iNN)",
                               1,
                               PyLong_FromUnsignedLongLong(m1.total_symbols),
                               PyLong_FromUnsignedLongLong(m1.total_steps));
          break;

        case RESULT_STEPPED:
          return Py_BuildValue("(iNN)",
                               2,
                               PyLong_FromUnsignedLongLong(m1.total_symbols),
                               PyLong_FromUnsignedLongLong(m1.total_steps));
          break;

        case RESULT_UNDEFINED:
          return Py_BuildValue("(iiiNN)",
                               3,m1.state,m1.symbol,
                               PyLong_FromUnsignedLongLong(m1.total_symbols),
                               PyLong_FromUnsignedLongLong(m1.total_steps));
          break;

        default:
          return Py_BuildValue("(iis)",-1,19,"Unexpected_result_for_fast_Turing_machine");
          break;
      }
    }
    else
    if ((result & RESULT_MACHINE) == RESULT_M2)
    {
      switch (result & RESULT_VALUE)
      {
        case RESULT_HALTED:
          return Py_BuildValue("(iNN)",
                               0,
                               PyLong_FromUnsignedLongLong(m2.total_symbols),
                               PyLong_FromUnsignedLongLong(m2.total_steps));
          break;

        case RESULT_NOTAPE:
          return Py_BuildValue("(iNN)",
                               1,
                               PyLong_FromUnsignedLongLong(m2.total_symbols),
                               PyLong_FromUnsignedLongLong(m2.total_steps));
          break;

        case RESULT_STEPPED:
          return Py_BuildValue("(iNN)",
                               2,
                               PyLong_FromUnsignedLongLong(m2.total_symbols),
                               PyLong_FromUnsignedLongLong(m2.total_steps));
          break;

        case RESULT_UNDEFINED:
          return Py_BuildValue("(iiiNN)",
                               3,m2.state,m2.symbol,
                               PyLong_FromUnsignedLongLong(m2.total_symbols),
                               PyLong_FromUnsignedLongLong(m2.total_steps));
          break;

        default:
          return Py_BuildValue("(iis)",-1,20,"Unexpected_result_for_slow_Turing_machine");
          break;
      }
    }
    else
    {
      return Py_BuildValue("(iis)",-1,21,"Normal_stop_but_not_machine_specific");
    }
  }

  return Py_BuildValue("(iis)",-1,22,"Reached_the_end_which_is_impossible,_;-)");
}
