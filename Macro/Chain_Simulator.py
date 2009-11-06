"""
Turing Machine Simulator with considerable accelleration due to tape compression
and chain moves.
"""

import math
import time

import Chain_Proof_System
import Chain_Tape
import Turing_Machine

DEBUG = False

# Infinite Reasons
PROOF_SYSTEM = "Proof_System"
REPEAT_IN_PLACE = "Repeat_in_Place"
CHAIN_MOVE = "Chain_Move"

class Simulator:
  """Turing machine simulator using chain-tape optimization."""
  def __init__(self):
    self.init_stats()
  
  def init(self, machine, recursive=False):
    """Default initialization, creates a blank tape, proof system, etc."""
    self.machine = machine
    self.tape = Chain_Tape.Chain_Tape()
    self.tape.init(machine.init_symbol, machine.init_dir)
    self.proof = Chain_Proof_System.Proof_System(self.machine, recursive)
    self.state = machine.init_state
    self.dir = machine.init_dir
    self.step_num = 0
    # Operation state (e.g. running, halted, proven-infinite, ...)
    self.op_state = Turing_Machine.RUNNING
    self.op_details = ()
    self.init_stats()
  
  def init_stats(self):
    """Initializes statistics about simulation."""
    self.num_loops = 0
    self.num_macro_moves = 0
    self.steps_from_macro = 0
    self.num_chain_moves = 0
    self.steps_from_chain = 0
    self.num_rule_moves = 0
    self.steps_from_rule = 0

  def run(self, steps):
    self.seek(self.step_num + steps)
  def seek(self, cutoff):
    """Run until we've reached (exceeded) step n."""
    while self.step_num < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()

  def loop_run(self, loops):
    """Loop through the step algorithm n times."""
    self.loop_seek(self.num_loops + loops)
  def loop_seek(self, cutoff):
    while self.num_loops < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()

  def true_loop_run(self, loops):
    self.true_loop_seek(self.num_loops + self.machine.num_loops + self.proof.num_loops + loops)
  def true_loop_seek(self, cutoff):
    """Like loop_seek except that it also considers loops through the proof system."""
    while self.num_loops + self.machine.num_loops + self.proof.num_loops < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()

  def step(self):
    """Perform an atomic transition or chain step."""
    if self.op_state != Turing_Machine.RUNNING:
      return
    self.num_loops += 1
    if self.proof:
      # Log the configuration and see if we can apply a rule.
      cond, new_tape, num_steps = self.proof.log(self.tape, self.state, self.step_num, self.num_loops-1)
      # Proof system says that machine will repeat forever
      if cond == Turing_Machine.INF_REPEAT:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = PROOF_SYSTEM
        return
      # Proof system says that we can apply a rule
      elif cond == Turing_Machine.RUNNING:
        if DEBUG:
          print
          print self.step_num, self.num_loops - 1
          print self.state, self.tape
        self.tape = new_tape
        self.step_num += num_steps
        self.num_rule_moves += 1
        self.steps_from_rule += num_steps
        if DEBUG:
          print self.state, self.tape
          print self.step_num, self.num_loops
        return
    # Get current symbol
    cur_symbol = self.tape.get_top_symbol()
    # Lookup TM transition rule
    cond, (symbol2write, next_state, next_dir), num_steps = \
          self.machine.get_transition(cur_symbol, self.state, self.dir)
    # Test condition
    self.op_state = cond[0]
    self.op_details = cond[1:]
    # Apply transition
    # Chain move
    if next_state == self.state and next_dir == self.dir and \
       self.op_state == Turing_Machine.RUNNING:
      num_reps = self.tape.apply_chain_move(symbol2write)
      if num_reps == Chain_Tape.INF:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = CHAIN_MOVE
        return
      # Don't need to change state or direction
      self.step_num += num_steps*num_reps
      self.num_chain_moves += 1
      self.steps_from_chain += num_steps*num_reps
    # Simple move
    else:
      self.tape.apply_single_move(symbol2write, next_dir)
      self.state = next_state
      self.dir = next_dir
      self.step_num += num_steps
      self.num_macro_moves += 1
      self.steps_from_macro += num_steps
      if self.op_state == Turing_Machine.INF_REPEAT:
        self.inf_reason = REPEAT_IN_PLACE
  
  def get_nonzeros(self):
    """Get Busy Beaver score, number of non-zero symbols on tape."""
    return self.tape.get_nonzeros(self.machine.eval_symbol,
                                  self.machine.eval_state(self.state))
  
  def print_self(self):
    x = len(repr(self.step_num)) + 1
    print
    print "         Steps:                       Times Applied:"
    print template("Total:", self.step_num, x, self.num_loops)
    #print "Single Steps:", with_power(self.mtt.num_single_steps)
    print template("Macro:", self.steps_from_macro, x, self.num_macro_moves) #, "Macro transitions defined:", len(self.mtt.macro_TTable)
    print template("Chain:", self.steps_from_chain, x, self.num_chain_moves)
    if self.proof:
      print template("Rule:", self.steps_from_rule, x, self.num_rule_moves)
      print "Rules proven:", len(self.proof.proven_transitions)
      print "Loops through prover:", self.proof.num_loops
    m = self.machine
    print "Loops through macro machine"
    while isinstance(m, Turing_Machine.Macro_Machine):
      print "", m.num_loops
      m = m.base_machine
    print "Time:", time.clock()
    print self.state, self.tape
    print "Num Nonzeros:", with_power(self.get_nonzeros())

def template(s, m, x, n):
  """Pretty printing function"""
  title = "%-8s" % s
  try:
    log_m = "10^%-6.1f" % math.log10(m)
  except:
    log_m = "         "
  m_str = "%-20s" % (("%%%dr" % x) % m)
    
  if len(m_str) > 20:
    m_str = " "*20
  n_str = "%12d" % n
  return title+" "+log_m+" "+m_str+" "+n_str

def with_power(value):
  """Pretty print helper. Print log(value) and value (if it's not too big)"""
  try:
    r = "10^%-6.1f " % math.log10(value)
  except:
    r = "        "
  value = str(value)
  if len(value) < 60:
    r += str(value)
  return r
