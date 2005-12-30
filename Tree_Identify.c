#include <Python.h>

#include "Turing_Machine.h"

static PyObject* Tree_Identify(PyObject* self,
                               PyObject* args);

static PyMethodDef Tree_Identify_Methods[] =
{
  { "Tree_Identify", Tree_Identify, METH_VARARGS, "Run Turing machine" },
  { NULL           , NULL         , 0           , NULL                 }
};

PyMODINIT_FUNC initTree_Identify(void)
{
  (void)Py_InitModule("Tree_Identify",Tree_Identify_Methods);
}

inline int find_pattern(TM*                 m_large,
                        unsigned long long  left_size,
                        unsigned long long  small_middle_size,
                        unsigned long long  large_middle_size,
                        unsigned long long* repeat_size,
                        unsigned long long* adjustment)
{
  unsigned long long cur_size;
  int* middle_start;
  int* previous;
  int* current;
  int repeat;

  *repeat_size = -1;
  *adjustment = 0;

  middle_start = m_large->tape + m_large->max_left + left_size;

  repeat = 0;
  for (cur_size = 1; cur_size <= small_middle_size; cur_size++)
  {
    unsigned long long scan;

    previous = middle_start;
    current = middle_start + cur_size;

    repeat = 1;
    for (scan = cur_size; scan < large_middle_size; scan++)
    {
      if (*previous != *current)
      {
        repeat = 0;
        break;
      }

      previous++;
      current++;
    }

    if (repeat == 1)
    {
      break;
    }
  }

  if (repeat == 1)
  {
    *repeat_size = cur_size;
    *adjustment = large_middle_size % cur_size;
  }

  return repeat;
}

static PyObject* Tree_Identify(PyObject* self,
                               PyObject* args)
{
  TM m1;
  TM m2;

  int result;

  unsigned long long step;
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

  unsigned long long left_pattern_start,left_pattern_end;

  unsigned long long middle_pattern_start,middle_pattern_end;
  unsigned long long repeat_size;

  unsigned long long right_pattern_start,right_pattern_end;

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

  left_pattern_start   = tape_middle;
  left_pattern_end     = tape_middle;

  middle_pattern_start = tape_middle;
  middle_pattern_end   = tape_middle;
  repeat_size = -1;

  right_pattern_start  = tape_middle;
  right_pattern_end    = tape_middle;

  for (step = 0; step < max_steps; step += 2)
  {
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
        unsigned long long scan_m1,scan_m2;
        unsigned long long left_start,left_end;
        unsigned long long right_start,right_end;

        while (m1.tape[m1.max_right] == 0 && m1.max_right > m1.position)
        {
          m1.max_right--;
        }

        while (m2.tape[m2.max_right] == 0 && m2.max_right > m2.position)
        {
          m2.max_right--;
        }

        scan_m1 = m1.max_left;
        scan_m2 = m2.max_left;

        while (scan_m1 < m1.max_right)
        {
          if (m1.tape[scan_m1] != m2.tape[scan_m2])
          {
            break;
          }

          scan_m1++;
          scan_m2++;
        }

        left_start = m1.max_left;
        left_end   = scan_m1 - 1;

        scan_m1 = m1.max_right;
        scan_m2 = m2.max_right;

        while (scan_m1 > m1.position)
        {
          if (m1.tape[scan_m1] != m2.tape[scan_m2])
          {
            break;
          }

          scan_m1--;
          scan_m2--;
        }

        right_start = scan_m1 + 1;
        right_end   = m1.max_right;

        if (right_start <= left_end)
        {
          unsigned long long left_size;
          unsigned long long small_middle_size;
          unsigned long long right_size;

          unsigned long long large_middle_size;

          unsigned long long adjustment;

          left_size = right_start - left_start;
          small_middle_size = left_end - right_start + 1;
          right_size = right_end - left_end;

          large_middle_size = m2.max_right - m2.max_left + 1 - 
                              (left_size + right_size);

          if (find_pattern(&m2,left_size,small_middle_size,large_middle_size,
                           &repeat_size,&adjustment) == 1)
          {
            left_pattern_start = left_start;
            left_pattern_end   = right_start - 1;

            middle_pattern_start = right_start;
            middle_pattern_end   = left_end - adjustment;

            right_pattern_start = left_end - adjustment + 1;
            right_pattern_end   = right_end;

            result = RESULT_INFINITE_TREE | RESULT_BOTH;
            break;
          }
        }
      }
    }
  }

  if ((result & RESULT_VALUE) == RESULT_INFINITE_TREE)
  {
    PyObject* left_list;
    PyObject* middle_list;
    PyObject* right_list;

    int left_size;
    int right_size;
    int middle_size;

    int i;

    int cur_step;

    left_size = left_pattern_end - left_pattern_start + 1;
    left_list = PyList_New(left_size);

    for (i = 0; i < left_size; i++)
    {
      PyList_SetItem(left_list,i,
                     Py_BuildValue("i",m1.tape[m1.max_left + i]));
    }

    middle_size = repeat_size;
    middle_list = PyList_New(middle_size);

    for (i = 0; i < middle_size; i++)
    {
      PyList_SetItem(middle_list,i,
                     Py_BuildValue("i",m1.tape[m1.max_left + left_size + i]));
    }

    right_size = right_pattern_end - right_pattern_start + 1;
    right_list = PyList_New(right_size);

    for (i = 0; i < right_size; i++)
    {
      PyList_SetItem(right_list,i,
                     Py_BuildValue("i",m1.tape[m1.max_right - right_size + 1 + i]));
    }

    cur_step = step+2;

    free_TM(&m1);
    free_TM(&m2);

    return Py_BuildValue("(NNN[ii])",left_list,middle_list,right_list,
                                     cur_step/2,cur_step);
  }
  else
  {
    free_TM(&m1);
    free_TM(&m2);

    return Py_BuildValue("()");
  }

  return Py_BuildValue("(iis)",-1,19,"Reached_the_end_which_is_impossible,_;-)");
}
