#include <Python.h>

typedef struct {
  int w;
  int d;
  int s;
} TRANSITION;

typedef struct {
  TRANSITION* t;
} STATE;

static PyObject* busyBeaverC_run(PyObject* self,
                                 PyObject* args);

static PyMethodDef busyBeaverCMethods[] =
{
  { "run", busyBeaverC_run, METH_VARARGS, "Run Turing machine" },
  { NULL , NULL           , 0           , NULL                 }
};

PyMODINIT_FUNC initbusyBeaverC(void)
{
  (void)Py_InitModule("busyBeaverC",busyBeaverCMethods);
}

static PyObject* busyBeaverC_run(PyObject* self,
                                 PyObject* args)
{
  int symbol,curSymbol;
  int state;
  int newSymbol;
  int newDelta;
  int newState;

  int                numSyms  = 0;
  unsigned long long numSteps = 0;

  double dNumSyms;
  double dNumSteps;

  unsigned long long i;
  int nTuple;

  PyObject* machineObj;
  STATE* machine = NULL;

  PyObject* numStatesObj;
  int numStates,numStatesImp;
  PyObject* numSymbolsObj;
  int numSymbols,numSymbolsImp;

  PyObject* tapeLengthObj;
  int tapeLength;
  int tapeStart = 0;
  int tapeEnd   = 0;
  int tapeMiddle;
  int tapePosition;
  int *tape = NULL;

  PyObject* maxStepsObj;
  unsigned long long maxSteps;

  int infinite;

  if (!PyTuple_CheckExact(args))
  {
    return Py_BuildValue("(iis)",-1,0,"Argument_was_not_a_tuple");
  }

  nTuple = PyTuple_Size(args);

  if (nTuple != 5)
  {
    return Py_BuildValue("(iis)",-1,1,"Expected_a_5-tuple_argument");
  }

  machineObj = PyTuple_GetItem(args,0);
  if (machineObj == NULL || !PyList_Check(machineObj))
  {
    return Py_BuildValue("(iis)",-1,2,"Unable_to_extract_Turing_machine");
  }

  numStatesObj = PyTuple_GetItem(args,1);
  if (numStatesObj == NULL || !PyInt_CheckExact(numStatesObj))
  {
    return Py_BuildValue("(iis)",-1,3,"Unable_to_extract_#_of_states");
  }

  numStates = PyInt_AsLong(numStatesObj);

  numSymbolsObj = PyTuple_GetItem(args,2);
  if (numSymbolsObj == NULL || !PyInt_CheckExact(numSymbolsObj))
  {
    return Py_BuildValue("(iis)",-1,4,"Unable_to_extract_#_of_symbols");
  }

  numSymbols = PyInt_AsLong(numSymbolsObj);

  numStatesImp = PyList_Size(machineObj);

  if (numStatesImp != numStates)
  {
    return Py_BuildValue("(iis)",-1,5,"Number_of_states_don't_match");
  }

  machine = (STATE *)malloc(numStates*sizeof(*machine));

  if (machine == NULL)
  {
    return Py_BuildValue("(iis)",-1,6,"Out_of_memory_allocating_'machine'");
  }

  for (state = 0; state < numStates; state++)
  {
    int curSymbol;
    PyObject* curStateObj;

    curStateObj = PyList_GetItem(machineObj,state);
    if (!PyList_Check(curStateObj))
    {
      return Py_BuildValue("(iis)",-1,7,"Unable_to_extract_Turing_machine_transition");
    }

    numSymbolsImp = PyList_Size(curStateObj);

    if (numSymbolsImp != numSymbols)
    {
      return Py_BuildValue("(iis)",-1,8,"Number_of_symbols_don't_match");
    }

    machine[state].t = (TRANSITION *)malloc(numSymbols*sizeof(*(machine[state].t)));
    if (machine[state].t == NULL)
    {
      return Py_BuildValue("(iis)",-1,9,"Out_of_memory_allocating_'machine'_state_transition");
    }

    for (curSymbol = 0; curSymbol < numSymbols; curSymbol++)
    {
      PyObject* curTransObj;
      int i0,i1,i2;

      curTransObj = PyList_GetItem(curStateObj,curSymbol);

      if (!PyTuple_CheckExact(curTransObj))
      {
        return Py_BuildValue("(iis)",-1,10,"Unable_to_extract_Turing_machine_transition_3-tuple");
      }

      if (PyTuple_Size(curTransObj) != 3)
      {
        return Py_BuildValue("(iis)",-1,11,"Turing_machine_transition_was_not_a_3-tuple");
      }

      if (!PyArg_ParseTuple(curTransObj,"iii",&i0,&i1,&i2))
      {
        return Py_BuildValue("(iis)",-1,12,"Unable_to_parse_Turing_machine_transition 3-tuple");
      }

      if (i0 < -1 || i0 >= numSymbols)
      {
        return Py_BuildValue("(iis)",-1,13,"Illegal_symbol_in_Turing_machine_transistion_3-tuple");
      }

      if (i1 < 0 || i1 > 1)
      {
        return Py_BuildValue("(iis)",-1,14,"Illegal_direction_in_Turing_machine_transistion_3-tuple");
      }

      if (i2 < -1 || i2 >= numStates)
      {
        return Py_BuildValue("(iis)",-1,15,"Illegal_state_in_Turing_machine_transistion_3-tuple");
      }

      machine[state].t[curSymbol].w = i0;
      machine[state].t[curSymbol].d = 2*i1 - 1;
      machine[state].t[curSymbol].s = i2;
    }
  }

  tapeLengthObj = PyTuple_GetItem(args,3);

  if (tapeLengthObj == NULL || !PyInt_CheckExact(tapeLengthObj))
  {
    return Py_BuildValue("(iis)",-1,16,"Unable_to_extract_tape_length");
  }

  tapeLength = PyInt_AsLong(tapeLengthObj);
  tapeMiddle = tapeLength / 2;

  tape = (int *)calloc(tapeLength,sizeof(*tape));

  if (tape == NULL)
  {
    return Py_BuildValue("(iis)",-1,17,"Out_of_memory_allocating_'tape'");
  }

  tapeStart    = tapeMiddle;
  tapeEnd      = tapeMiddle;
  tapePosition = tapeMiddle;

  maxStepsObj = PyTuple_GetItem(args,4);

  if (maxStepsObj == NULL || !PyFloat_CheckExact(maxStepsObj))
  {
    return Py_BuildValue("(iis)",-1,18,"Unable_to_extract_maximum_#_of_steps");
  }

  maxSteps = PyFloat_AsDouble(maxStepsObj);

  state  = 0;
  symbol = tape[tapePosition];

  newState  = -1;
  newSymbol = -1;

  numSyms  = 0;
  numSteps = 0;

  infinite = 0;
  newDelta = 0;

  for (i = 0; i < maxSteps; i++)
  {
    numSteps++;

    symbol = tape[tapePosition];

    newSymbol = machine[state].t[symbol].w;
    newDelta  = machine[state].t[symbol].d;
    newState  = machine[state].t[symbol].s;

    if (newSymbol < 0) {
      break;
    }

    if (symbol == 0 && newSymbol != 0)
    {
      numSyms++;
    }

    if (symbol != 0 && newSymbol == 0)
    {
      numSyms--;
    }

    tape[tapePosition] = newSymbol;
    tapePosition += newDelta;

    if (newState == -1)
    {
      break;
    }

    if (tapePosition < 1 || tapePosition >= tapeLength-1)
    {
      break;
    }

    if (tapePosition < tapeStart)
    {
      tapeStart = tapePosition;

      if (symbol == 0 && newState == state && newDelta == -1) {
        infinite = 1;
        break;
      }
    }

    if (tapePosition > tapeEnd)
    {
      tapeEnd = tapePosition;

      if (symbol == 0 && newState == state && newDelta == 1) {
        infinite = 1;
        break;
      }
    }

    state = newState;
  }

  curSymbol = tape[tapePosition];

  if (machine != NULL)
  {
    int s;
    for (s = 0; s < numStates; s++)
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

  dNumSyms  = numSyms;
  dNumSteps = numSteps;

  if (infinite == 1) {
    if (newDelta == -1) {
      return Py_BuildValue("(iis)",4,0,"Infinite_left");
    } else {
      return Py_BuildValue("(iis)",4,1,"Infinite_right");
    }
  }

  if (newState == -1)
  {
    if (newSymbol >= 0)
    {
      return Py_BuildValue("(idd)",0,dNumSyms,dNumSteps);
    }
    else
    {
      return Py_BuildValue("(iiiidd)",3,state,symbol,curSymbol,
                                        dNumSyms,dNumSteps-1);
    }
  }

  if (i < maxSteps)
  {
    return Py_BuildValue("(idd)",1,dNumSyms,dNumSteps);
  }
  else
  {
    return Py_BuildValue("(idd)",2,dNumSyms,dNumSteps);
  }

  return Py_BuildValue("(iis)",-1,19,"Reached_the_end_which_is_impossible,_;-)");
}
