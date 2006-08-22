"""
Turing Machine Simulator with considerable accelleration due to tape compression and chain moves.
"""

import Turing_Machine, Chain_Tape, Chain_Proof_System
import time, math

# Infinite Reasons
PROOF_SYSTEM = "Proof_System"
REPEAT_IN_PLACE = "Repeat_in_Place"
CHAIN_MOVE = "Chain_Move"


class Simulator:
  def __init__(self):
    self.init_stats()
  def init(self, machine, recursive=False):
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
    while self.step_num < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()
  def loop_run(self, loops):
    self.loop_seek(self.num_loops + loops)
  def loop_seek(self, cutoff):
    while self.num_loops < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()
  def true_loop_run(self, loops):
    self.true_loop_seek(self.num_loops + self.machine.num_loops + self.proof.num_loops + loops)
  def true_loop_seek(self, cutoff):
    while self.num_loops + self.machine.num_loops + self.proof.num_loops < cutoff and self.op_state == Turing_Machine.RUNNING:
      self.step()
  def step(self):
    """Perform an atomic transition or chain step."""
    if self.op_state != Turing_Machine.RUNNING:
      return
    self.num_loops += 1
    if self.proof:
      #if self.proof.num_loops > self.num_loops:
      #  self.proof.prev_configs = {}
      #else:
        cond, new_tape, num_steps = self.proof.log(self.tape, self.state, self.step_num)
        if cond == Turing_Machine.INF_REPEAT:
          self.op_state = Turing_Machine.INF_REPEAT
          self.inf_reason = PROOF_SYSTEM
          return
        elif cond == Turing_Machine.RUNNING:
          self.tape = new_tape
          self.step_num += num_steps
          self.num_rule_moves += 1
          self.steps_from_rule += num_steps
          return
    # Get current symbol
    cur_symbol = self.tape.get_top_symbol()
    # Get transition
    cond, (symbol2write, next_state, next_dir), num_steps = \
          self.machine.get_transition(cur_symbol, self.state, self.dir)
   # Test condition
    self.op_state = cond[0]
    self.op_details = cond[1:]
    # Apply transition
    if next_state == self.state and next_dir == self.dir and \
       self.op_state == Turing_Machine.RUNNING:
      # Apply chain move
      num_reps = self.tape.apply_chain_move(symbol2write)
      if num_reps == Chain_Tape.INF:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = CHAIN_MOVE
        return
      # Don't need to change state or direction
      self.step_num += num_steps*num_reps
      self.num_chain_moves += 1
      self.steps_from_chain += num_steps*num_reps
      pass
    else:
      # Apply simple move
      self.tape.apply_single_move(symbol2write, next_dir)
      self.state = next_state
      self.dir = next_dir
      self.step_num += num_steps
      self.num_macro_moves += 1
      self.steps_from_macro += num_steps
      if self.op_state == Turing_Machine.INF_REPEAT:
        self.inf_reason = REPEAT_IN_PLACE
  def get_nonzeros(self):
    return self.tape.get_nonzeros(self.machine.eval_symbol,
                                  self.machine.eval_state(self.state))
  def print_self(self):
    x = int(math.log10(self.step_num + 1)) + 1
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
  title = "%-8s" % s
  try:
    log_m = "10^%-6.1f" % math.log10(m)
  except:
    log_m = "         "
  m_str = "%-20s" % (("%%%dd" % x) % m)
  if len(m_str) > 20:
    m_str = " "*20
  n_str = "%12d" % n
  return title+" "+log_m+" "+m_str+" "+n_str

def with_power(value):
  try:
    r = "10^%-6.1f " % math.log10(value)
  except:
    r = "        "
  value = str(value)
  if len(value) < 60:
    r += str(value)
  return r
