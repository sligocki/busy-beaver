#! /usr/bin/env python

import sys
sys.path.append("..")
from IO import IO
from Turing_Machine import Turing_Machine
from Turing_Machine_Sim import Turing_Machine_Sim

def Eval_Machine(ttable):
  """
  Find the Multiplicity of given machine.
  Multiplicity = # of machines that this is equivolent to.
  """
  machine = Turing_Machine(ttable)
  sim = Turing_Machine_Sim(machine)
  m = machine.num_states
  p = machine.num_symbols

  multiple = 1
  # d(A, 0) = ([^HA], [^0], *) -> Mirror copy of all machines
  multiple *= (m-1)*(p-1)*2

  max_state = max_symbol = 1
  reached_cells = [(sim.state, sim.symbol)]
  # 'i' = cell number, ranges from 0 -> number of cells reached.
  for i in range(m*p - machine.num_empty_cells - 1):
    cell_pos = sim.state, sim.symbol
    while cell_pos in reached_cells:
      sim.step()
      cell_pos = sim.state, sim.symbol
#    print cell_pos, sim.step_num, multiple, reached_cells
    reached_cells.append(cell_pos)
    new_state, new_direction, new_symbol = sim.get_current_cell()
#    print new_state, max_state, new_symbol, max_symbol
    if new_state > max_state:
      multiple *= m - max_state
      max_state = new_state
    if new_symbol > max_symbol:
      multiple *= p - max_symbol
      max_symbol = new_symbol
  multiple *= ((m+1)*p*2)**machine.num_empty_cells

  return multiple

def Eval_Machines(machines):
  # Get a sample machine and sample the num of states and symbols.
  ttable = machines[10][0]
  m = len(ttable)
  p = len(ttable[0])

  total_count = ((m+1)*p*2)**(m*p)
  result = {}
  # Defined: d(A, 0) = (B, 1, R)
  # d(A, 0) = (H, *, *) -> Halt w/ 1 step and 0,1 symbols
  result["halt"] = p*2*((m+1)*p*2)**(m*p - 1)
  # d(A, 0) = (A, *, *) -> Repeat forever step=1
  result["infinite"] = p*2*((m+1)*p*2)**(m*p - 1)
  # d(A, 0) = ([^HA], 0, *) -> Unexplored
  result["unexplored"] = (m-1)*2*((m+1)*p*2)**(m*p - 1)
  result["unknown"] = 0

  for machine, outcome in machines:
    result[outcome] += Eval_Machine(machine)

  return result, sum(result.values()), total_count

def Get_File(filename, outcome):
  infile = file(filename)
  io = IO(infile, None)
  machines = []
  line = io.read_result()
  while line:
    ttable = line[6]
    machines.append((ttable, outcome))
    line = io.read_result()
  return machines

def Get_Machines(halt_fn, infinite_fn, unknown_fn):
  machines = Get_File(halt_fn, "halt")
  machines += Get_File(infinite_fn, "infinite")
  machines += Get_File(unknown_fn, "unknown")
  return machines

def Enumerate_Machine(ttable):
  num_states = len(ttable) + 1
  num_symbols = len(ttable[0])
  enum = 0
  # States are the rows of the transition table
  for row in ttable:
    # Symbols are the columns of the transition table
    for cell in row:
      symbol, direction, state = cell
      if state == -1:
        # We consider the halting state to be the last state here.
        state = num_states - 1
      if symbol not in range(num_symbols) or \
         state not in range(num_states) or \
         direction not in range(2):
        raise ValueError, "Enumerate_Machine -- ttable cell ("+`cell`+") invalid."
      # Encodes cell into a number 0->2mp - 1 (Total possible cells)
      enum = num_symbols*enum + symbol
      enum = 2*enum           + direction
      enum = num_states*enum  + state
  return enum

def Unenumerate_Machine(enum, num_states, num_symbols):
  ttable = [None] * num_states
  for i in range(num_states):
    ttable[i] = [None] * num_symbols
  for row in range(num_states - 1, -1, -1):
    for column in range(num_symbols - 1, -1, -1):
      state = enum % (num_states+1); enum //= (num_states+1)
      direction = enum % 2;          enum //= 2
      symbol = enum % num_symbols;   enum //= num_symbols
      if state == num_states:
        state = -1
      ttable[row][column] = (symbol, direction, state)
  if enum:
    print ttable
    raise ValueError, "Unenumerate_Machine -- enum to large to encode machine"
  return ttable

if __name__ == "__main__":
  import sys
  try:
    basename = sys.argv[1]
  except:
    basename = "../Data/2.2.100000.100000"
  machines = Get_Machines(basename+".halt", basename+".infinite",
                          basename+".unknown")
#  print machines[20]
  evaluation = Eval_Machines(machines)
  print evaluation
