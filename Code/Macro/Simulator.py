#
# Simulator.py
#
"""
Turing Machine Simulator with considerable accelleration due to tape
compression, chain moves and a proof system.
"""

import math
import optparse
from optparse import OptionParser, OptionGroup
import sys
import time

import Proof_System
import Tape
import Turing_Machine

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
from Numbers.Algebraic_Expression import Algebraic_Expression

def add_option_group(parser):
  """Add Simulator options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  Turing_Machine.add_option_group(parser)
  Proof_System.add_option_group(parser)

  group = OptionGroup(parser, "Simulator options")

  group.add_option("--verbose-simulator", action="store_true")
  group.add_option("--no-steps", dest="compute_steps",
                    action="store_false", default=True,
                    help="Don't keep track of base step count (can be "
                   "expensive to calculate especially with recursive proofs).")
  group.add_option("-p", "--no-prover", dest="prover",
                   action="store_false", default=True,
                   help="Turn OFF proof system.")
  group.add_option("--html-format", action="store_true",
                   help="Print tape in an HTML format.")

  parser.add_option_group(group)

def create_default_options():
  """Returns a set of default options."""
  parser = OptionParser()
  add_option_group(parser)
  options, args = parser.parse_args([])
  return options

# Infinite Reasons
PROOF_SYSTEM = "Proof_System"
REPEAT_IN_PLACE = "Repeat_in_Place"
CHAIN_MOVE = "Chain_Move"

class Simulator(object):
  """Turing machine simulator using chain-tape optimization."""
  def __init__(self, machine, options, verbose_prefix="", init_tape=True):
    assert isinstance(options, optparse.Values)

    self.machine = machine
    self.options = options
    self.compute_steps = options.compute_steps
    self.verbose = options.verbose_simulator
    self.verbose_prefix = verbose_prefix

    self.state = machine.init_state
    self.dir = machine.init_dir
    self.old_step_num = 0
    self.step_num = 0

    # Init tape and prover (if needed).
    if init_tape:
      self.tape = Tape.Chain_Tape()
      self.tape.init(self.machine.init_symbol, self.machine.init_dir, options)
    if options.prover:
      self.prover = Proof_System.Proof_System(machine=self.machine,
                                              options=self.options,
                                              verbose_prefix=self.verbose_prefix + "  ")
    else:
      self.prover = None  # We will run the simulation without a proof system.

    # Set of variables to replace (needed for Simulator in Proof_System when
    # Collatz-style rules are allowed).
    self.replace_vars = {}

    # Operation state (e.g. running, halted, proven-infinite, ...)
    self.op_state = Turing_Machine.RUNNING
    self.op_details = ()

    # Stats
    self.states_used = set()
    self.num_loops = 0
    self.num_macro_moves = 0
    self.num_chain_moves = 0
    self.num_rule_moves = 0
    if self.compute_steps:
      self.steps_from_macro = 0
      self.steps_from_chain = 0
      self.steps_from_rule = 0
    else:
      self.steps_from_macro = None
      self.steps_from_chain = None
      self.steps_from_rule = None

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

  # TODO: true_loop_run which captures cost of prover, etc. also.

  def step(self):
    """Perform an atomic transition or chain step."""
    if self.op_state != Turing_Machine.RUNNING:
      return

    if self.compute_steps:
      self.old_step_num = self.step_num
    # Note: We increment the number of loops early to take care of all the
    # places step() could early-return.
    self.num_loops += 1
    if self.prover:
      # Log the configuration in the prover and apply rule if possible.
      prover_result = self.prover.log_and_apply(
        self.tape, self.state, self.step_num, self.num_loops-1)

      # Proof system says that machine will repeat forever
      if prover_result.condition == Proof_System.INF_REPEAT:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = PROOF_SYSTEM
        # Get set of states which will *not* be used in this infinite repeat.
        self.inf_states_unused = \
          set(self.machine.list_base_states()) - prover_result.states_used
        self.verbose_print()
        return
      # Proof system says that we can apply a rule
      elif prover_result.condition == Proof_System.APPLY_RULE:
        # TODO(shawn): This seems out of place here and is the only place in
        # the Simulator where we distinguish Algebraic_Expressions.
        # We should clean it up in some way.
        if prover_result.replace_vars:
          assert self.options.allow_collatz
          # We don't want the update below to overwrite things.
          assert not frozenset(self.replace_vars.keys()).intersection(
                     frozenset(prover_result.replace_vars.keys()))
          self.replace_vars.update(prover_result.replace_vars)
          # Update all instances of old variable (should just be in steps).
          assert isinstance(self.step_num, Algebraic_Expression)
          self.step_num = self.step_num.substitute(prover_result.replace_vars)
          assert isinstance(self.old_step_num, Algebraic_Expression)
          self.old_step_num = self.old_step_num.substitute(prover_result.replace_vars)
          assert not isinstance(self.num_loops, Algebraic_Expression)
        self.tape = prover_result.new_tape
        self.num_rule_moves += 1
        self.states_used.update(prover_result.states_used)
        if self.compute_steps:
          self.step_num += prover_result.num_base_steps
          self.steps_from_rule += prover_result.num_base_steps
        self.verbose_print()
        return
    # Get current symbol
    cur_symbol = self.tape.get_top_symbol()
    # Lookup TM transition rule
    trans = self.machine.get_trans_object(cur_symbol, self.state, self.dir)
    self.op_state = trans.condition
    self.op_details = trans.condition_details
    # Apply transition
    # Chain move
    if trans.state_out == self.state and trans.dir_out == self.dir and \
       self.op_state == Turing_Machine.RUNNING:
      num_reps = self.tape.apply_chain_move(trans.symbol_out)
      if num_reps == Tape.INF:
        self.op_state = Turing_Machine.INF_REPEAT
        self.inf_reason = CHAIN_MOVE
        # Get set of states which will *not* be used in this infinite repeat.
        self.inf_states_unused = \
          set(self.machine.list_base_states()) - trans.states_used
        self.verbose_print()
        return
      # Don't need to change state or direction
      self.num_chain_moves += 1
      self.states_used.update(trans.states_used)
      if self.compute_steps:
        self.step_num += trans.num_base_steps * num_reps
        self.steps_from_chain += trans.num_base_steps * num_reps
    # Simple move
    else:
      self.tape.apply_single_move(trans.symbol_out, trans.dir_out)
      self.state = trans.state_out
      self.dir = trans.dir_out
      self.num_macro_moves += 1
      self.states_used.update(trans.states_used)
      if self.compute_steps:
        self.step_num += trans.num_base_steps
        self.steps_from_macro += trans.num_base_steps
      if self.op_state == Turing_Machine.INF_REPEAT:
        self.inf_reason = REPEAT_IN_PLACE
        # Get set of states which will *not* be used in this infinite repeat.
        self.inf_states_unused = \
          set(self.machine.list_base_states()) - trans.states_used
    if self.op_state != Turing_Machine.UNDEFINED:
      self.verbose_print()

  def get_nonzeros(self):
    """Get Busy Beaver score, number of non-zero symbols on tape."""
    return self.tape.get_nonzeros(self.machine.eval_symbol,
                                  self.machine.eval_state(self.state))

  def print_self(self):
    self.print_steps()
    print "Time:", time.clock()
    print self.tape.print_with_state(self.state)
    print "Num Nonzeros:", with_power(self.get_nonzeros())

  def print_steps(self):
    print
    print "         Steps:                     Times Applied:"
    print template("Total:", self.step_num, self.num_loops)
    #print "Single Steps:", with_power(self.mtt.num_single_steps)
    print template("Macro:", self.steps_from_macro, self.num_macro_moves)
    #print "Macro transitions defined:", len(self.mtt.macro_TTable)
    print template("Chain:", self.steps_from_chain, self.num_chain_moves)
    if self.prover:
      print template("Rule:", self.steps_from_rule, self.num_rule_moves)
      print "Rules proven:", len(self.prover.rules)
      if self.prover.recursive:
        print "Recursive rules proven:", self.prover.num_recursive_rules
        if self.prover.allow_collatz:
          print "Collatz rules proven:", self.prover.num_collatz_rules
      print "Failed proofs:", self.prover.num_failed_proofs
    print "Tape copies:", Tape.Chain_Tape.num_copies

  def verbose_print(self):
    if self.verbose:
      if self.options.html_format:
        print "%s %6d: %s<br>" % (self.verbose_prefix, self.step_num,
                                  self.tape.print_with_state(self.state))
      else:
        print "%s %6d  %s" % (self.verbose_prefix, self.num_loops, self.tape.print_with_state(self.state)),
        if self.compute_steps:
          print "(%s, %s)" % (self.step_num - self.old_step_num, self.step_num)
        else:
          print ""

def template(title, steps, loops):
  """Pretty print row of the steps table."""
  return "%-8s %-20s %20d" % (title, format_power(steps), loops)

def with_power(value, max_width=60):
  """Pretty print log(value) and value (if it's not too big)"""
  output = format_power(value) + "  "

  value_string = str(value)
  if len(output) + len(value_string) < max_width:
    output += value_string
  else:
    margin = (max_width - len(output) - 2) // 2
    if margin > 0:
      output += value_string[:margin] + ".." + value_string[-margin:]

  return output

def format_power(value):
  """Pretty print 'value' in exponential notation."""
  try:
    return "10^%.1f" % math.log10(value)
  except:
    return ""
