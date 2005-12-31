import sys, copy

def Tree_Classify(machine, (L, MR, R, initial_steps)):
  """Tree_Clasify is the 2nd function in the proving that a turing machine
  exhibits tree behavior and hence will not halt."""
  while len(L) > 0 and L[0] == 0:
    del L[0]
  while len(R) > 0 and R[-1] == 0:
    del R[-1]
  L2_begin = initial_steps[-2]
  L1_end = initial_steps[-1]
  sim = Turing_Machine_Sim(machine)
  sim.seek(L2_begin)
  print " ", L, MR, R
  print " ", sim.tape, sim.position, sim.step_num
  L_max, R_min = get_bounds(sim.tape, L, R)
  MR_begin = last_visit_before(sim, L_max, R_min) + 1
  if MR_begin is None:
    MR_begin = L2_begin
    raise ValueError, "Machine fails to reach middle of tape."
  sim.seek(MR_begin)
  print "  MR_begin =", MR_begin
  MR_, position_shift = Find_Repeat(sim)
  # These should be equal, if not we have defined M incorrectly.
  if position_shift != len(MR):
    # if len(MR) | position_shift
    if position_shift % len(MR) == 0:
      MR = MR * (position_shift // len(MR))
    else:
      print "Detected temporal repeat does not match spacial repeat. %d != %d\n" % (position_shift, len(MR))
      raw_input("?")
      #raise ValueError, "Detected temporal repeat does not match spacial repeat. %d != %d\n" % (position_shift, len(MR))

  # 'head' is the furthest forward that will affect the machine in the next
  # repetition.  'tail' is the furthest back equivolently.
  head = sim.position + (len(MR_[0][0]) - MR_[0][1] - 1)
  steps = sim.step_num
  L2_ = get_neighborhood(sim, L2_begin, MR_begin)
  macro_steps = (R_min - head) // position_shift
  R_begin = steps + macro_steps*MR_[1]

  sim.seek(R_begin)
  ML_begin = last_visit_before(sim, R_min, L_max) + 1
  if ML_begin is None:
    ML_begin = R_begin
    raise ValueError, "Machine fails to reach middle of tape."
  sim.seek(ML_begin)
  ML_, position_shift = Find_Repeat(sim)
  ML_len = position_shift

  head = sim.position - (ML_[0][1])
  steps = sim.step_num
  R_ = get_neighborhood(sim, R_begin, ML_begin)
  macro_steps = (head - L_max) // -position_shift
  L1_begin = steps + macro_steps*ML_[1]
  L1_ = get_neighborhood(sim, L1_begin, L1_end)

  sim.seek(L2_begin)
  if sim.position + (len(L2_[0][0]) - L2_[0][1]) >= R_min:
    print "L2_ is hugenormous."
    raw_input("?")
    return None
  sim.seek(R_begin)
  if sim.position - (R_[0][1]) <= L_max:
    print "R_ is hugenormous."
    raw_input("?")
    return None
  sim.seek(L1_begin)
  if sim.position + (len(L1_[0][0]) - L1_[0][1]) >= R_min:
    print "L1_ is hugenormous."
    raw_input("?")
    return None

  return (L, MR, R, ML_len, initial_steps), (L2_, MR_, R_, ML_, L1_)

def get_neighborhood(sim, begin, end):
  """Get the neighborhood which machine traverses between begin and end
  inclusive.  end >= begin."""
  if end < begin:
    raise ValueError, "get_neighborhood -- end must not be less than begin."
  sim.seek(begin)
  nbh = (sim.position, sim.position)
  for i in range(begin, end):
    sim.run(1)
    nbh = (min(sim.position, nbh[0]), max(sim.position, nbh[1]))
  if sim.step_num != end:
    print sim.step_num, end
    raise ValueError, "WTF?"
  final_nbh = sim.tape[nbh[0]:nbh[1]+1]
  final_pos = sim.position - nbh[0]
  sim.seek(begin)
  initial_nbh = sim.tape[nbh[0]:nbh[1]+1]
  initial_pos = sim.position - nbh[0]
  return ((initial_nbh, initial_pos), end - begin, (final_nbh, final_pos))

def last_visit_before(sim, start, end):
  """Returns the step number of the last time that machine was at position
  start before reaching end.  Since machine can only make one step at a time
  this will tell you the last time it's in one region before entering another.
  Returns None if never visited start before reaching end."""
  last_visit = None
  if sim.position == start:
    last_visit = sim.step_num
  while sim.position != end:
    sim.run(1)
    if sim.position == start:
      last_visit = sim.step_num
  return last_visit

def get_bounds(tape, L, R):
  """Check that L and R are on the ends of tape and return their boundries
  with the middle."""
  right = tape.right()
  R_min = right+1 - len(R)
  if tape[R_min : right+1] != R:
    raise ValueError, "Tree_Classify -- R not on right of tape."
  left = tape.left()
  L_max = left + len(L)
  if tape[left : L_max] != L:
    raise ValueError, "Tree_Classify -- L not on left of tape."
  return L_max, R_min
    

def Find_Repeat(sim):
  """Given a simulator assumed to be in the "M-region", finds the neighborhood
  and number of steps """
  # 'sim2' is a snapshot of 'sim' used for comparison purposes only.
  sim2 = copy.deepcopy(sim)
  # 'nbh' (neighborhood) records the left-most and right-most positions
  # reached.  The neighborhood which affected running so far.
  nbh = (sim2.position, sim2.position)
  while True:
    sim2.run(1)
    # 'nbh' has min and max position reached.
    nbh = (min(sim2.position, nbh[0]), max(sim2.position, nbh[1]))
    rel_pos = sim2.position - sim.position
    # Compare "neighborhood configurations" of 'sim2' and 'sim'
    # Currently inefficient?  Instead of comparing neighborhoods one element
    # at a time, it computes entire neighborhoods for each and compares.
    if sim.state  == sim2.state and \
       sim.tape[nbh[0]:nbh[1]+1] == sim2.tape[nbh[0]+rel_pos : nbh[1]+rel_pos+1]:
      initial_nbh = sim.tape[nbh[0]:nbh[1]+1]
      initial_pos = sim.position - nbh[0]
      steps = sim2.step_num - sim.step_num
      final_nbh = sim2.tape[nbh[0]:nbh[1]+1]
      final_pos = sim2.position - nbh[0]
      return (((initial_nbh, initial_pos), steps, (final_nbh, final_pos)),
              rel_pos)


class Tape:
  """Class for a turing machine's tape."""
  def __init__(self, start = 0, stop = 0, val = []):
    self.tape = {}
    self[start:stop] = val
  def left(self):
    """Return index of left-most non-zero item."""
    try:
      return min(self.tape.keys())
    except ValueError:
      return None
  def right(self):
    """Return index of right-most non-zero item."""
    try:
      return max(self.tape.keys())
    except ValueError:
      return None
  def __repr__(self):
    left  = self.left()
    right = self.right()
    if None in [left, right]:
      return "Tape()"
    else:
      return "Tape(%d, %d, %s)" % (left, right+1, `self[left : right+1]`)
  def __cmp__(self, tape2):
    """Good for == and !=, but relatively meaningless for <, >, etc."""
    for key in self.tape:
      if self[key] != tape2[key]:
        return self[key] - tape2[key]
    return 0
  def __getitem__(self, pos):
    """Read symbol on tape at position.  Tape is assumed to have 0's
    everywhere not yet defined/set."""
    return self.tape.get(pos, 0)
  def __setitem__(self, pos, val):
    """Write symbol on tape at position."""
    if type(pos) in [int, long]:
      if val != 0:
        self.tape[pos] = val
      # if val == 0 and tape[pos] != 0
      elif self.tape.has_key(pos):
        del self.tape[pos]
    else:
      raise ValueError, "Tape.__setitem__ -- index (%s) must be an integer." % repr(pos)
  def __delitem__(self, pos):
    self[pos] = 0
  def __getslice__(self, start, stop):
    """Read symbols on slice of tape."""
    return [self[i] for i in range(start, stop)]
  def __setslice__(self, start, stop, val):
    """Write symbols to slice of tape."""
    if len(val) != stop - start:
      raise ValueError, "Slices must be replaced by lists of the same length"
    else:
      for i in range(stop - start):
        self[i + start] = val[i]
  def __len__(self):
    """Defined so that slices and negative indeces will work correctly."""
    return 0

class Turing_Machine_Sim:
  """Class for simulating Turing Machines.
  Initialized by a Turing Machine and an initial tape."""
  def __init__(self, machine, tape = None, position = 0, state = 0):
    # Set read-only attributes which describe initial values of system.
    self.machine = machine
    if not tape:
      tape = Tape()
    self.initial_tape = tape
    self.initial_position = position
    self.initial_state = state
    # Set mutable attributes which will be altered as machine is progressed.
    self.restart()

  def restart(self):
    """Restarts Turing Machine to initial conditions."""
    self.tape = copy.deepcopy(self.initial_tape)
    self.position = self.initial_position
    self.state = self.initial_state
    self.symbol = self.tape[self.position]
    self.step_num = 0

  def seek(self, step_num):
    """Seeks a given step number in TM run."""
    if step_num >= self.step_num:
      self.run(step_num - self.step_num)
    elif step_num >= 0:
      self.restart()
      self.run(step_num)
    else:
      raise ValueError, "Turing_Machine_Sim.seek -- step_num (%d) must not be negative" % step_num

  def run(self, steps, pos_return = None):
    """Runs Turing Machine n steps further or until pos_return is reached,
    whichever comes first.
    
    If pos_return is reached returns True, otherwise returns None."""
    if steps < 0:
      self.seek(self.step_num - steps)
    else:
      for i in xrange(steps):
        self.step(self.machine.get_cell(self.state, self.symbol))
        if self.position == pos_return:
          return True

  def step(self, (symbol, direction, state)):
    """Applies a single step in running the TM."""
    # Write symbol.
    self.tape[self.position] = symbol
    # Move one step in given direction.
    if direction:
      self.position += 1
    else:
      self.position -= 1
    # Update symbol
    self.symbol = self.tape[self.position]
    # Change state.
    self.state = state
    # Increment number of steps taken
    self.step_num += 1
