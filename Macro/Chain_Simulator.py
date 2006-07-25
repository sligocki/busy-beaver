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
  def init(self, machine):
    self.machine = machine
    self.tape = Chain_Tape.Chain_Tape()
    self.tape.init(machine.init_symbol, machine.init_dir)
    self.proof = Chain_Proof_System.Proof_System(self.machine, False)
    self.state = machine.init_state
    self.dir = machine.init_dir
    self.step_num = 0
    # Operation state (e.g. running, halted, proven-infinite, ...)
    self.op_state = Turing_Machine.RUNNING
  def run(self, steps):
    self.seek(self.step_num + steps)
  def seek(self, cutoff):
    while self.step_num < cutoff and self.op_state is Turing_Machine.RUNNING:
      self.step()
  def step(self):
    """Perform an atomic transition or chain step."""
    if self.op_state is not Turing_Machine.RUNNING:
      return
    if self.proof:
      cond, new_tape, num_steps = self.proof.log(self.tape, self.state, self.step_num)
      if cond is Turing_Machine.INF_REPEAT:
        op_state = Turing_Machine.INF_REPEAT
        inf_reason = PROOF_SYSTEM
        return
      elif cond is Turing_Machine.RUNNING:
        self.tape = new_tape
        self.step_num += num_steps
        return
    # Get current symbol
    cur_symbol = self.tape.get_top_symbol()
    # Get transition
    cond, (symbol2write, next_state, next_dir), num_steps = \
          self.machine.get_transition(cur_symbol, self.state, self.dir)
   # Test condition
    self.op_state = cond[0]
    if self.op_state is Turing_Machine.UNDEFINED:
      return
    # Apply transition
    if next_state == self.state and next_dir == self.dir and \
       self.op_state is Turing_Machine.RUNNING:
      # Apply chain move
      num_reps = self.tape.apply_chain_move(symbol2write)
      if num_reps == Chain_Tape.INF:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = CHAIN_MOVE
        return
      # Don't need to change state or direction
      self.step_num += num_steps*num_reps
      pass
    else:
      # Apply simple move
      self.tape.apply_single_move(symbol2write, next_dir)
      self.state = next_state
      self.dir = next_dir
      self.step_num += num_steps
      if self.op_state is Turing_Machine.INF_REPEAT:
        self.inf_reason = REPEAT_IN_PLACE
  def get_nonzeros(self):
    return self.tape.get_nonzeros(self.machine.eval_symbol,
                                  self.machine.eval_state(self.state))
  def print_self(self):
    print
    print "Total Steps: ", with_power(self.step_num)
    print "Time:", time.clock()
    print self.state, self.tape, self.get_nonzeros()

def with_power(value):
  if value is Chain_Tape.INF:
    r = "10^Inf  "
  elif value == 0:
    r = "10^-Inf "
  else:
    try:
      r = "10^%-4.1f " % math.log10(value)
    except:
      r = "        "
  value = str(value)
  if len(value) < 60:
    r += str(value)
  return r
