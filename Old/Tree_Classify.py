import copy
import Turing_Machine_Sim

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
