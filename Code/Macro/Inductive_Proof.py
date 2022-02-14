"""
Inductive proofs use a simpler form of the rule they are proving in the proof.

For example, consider this proof:

X 0 1^2k+1 B> 0 Y  ->  X 1^2k+3 B> Y  in F(k) steps

X 0 1^2k+1 B> 0 Y
X 0 1^2k+1 <C 1 Y         1
X 0 1^2k <D 0 1 Y         1
X 0 <D 1^2k 0 1 Y        2k
X 1 A> 1^2k 0 1 Y         1
X 1 0 B> 1^2k-1 0 1 Y     1
X 1 0 1^2k-1 B> 0 1 Y  2k-1
  Applying inductive hypothesis
X 1 1^2k+1 B> 1 Y    F(k-1)
X 1^2k+3 B> Y             1
"""

import copy
import sys

from Macro import Proof_System
from Macro import Simulator

parent_dir = sys.path[0][:sys.path[0].rfind("/")] # pwd path with last directory removed
sys.path.insert(1, parent_dir)
from Numbers import Algebraic_Expression

def Inductive_Proof(machine, options, rule):
  assert isinstance(rule, Proof_System.General_Rule)

  # Construct simulator
  new_options = copy.copy(options)
  new_options.recursive = False
  #new_options.prover = False
  sim = Simulator.Simulator(machine, new_options, init_tape=False)
  #                         verbose_prefix=self.verbose_prefix + "  ")
  sim.step_num = Algebraic_Expression.ConstantToExpression(0)

  # Initialize simulator to start config.
  start_config = rule.start_config()
  sim.state = start_config.state
  sim.tape = start_config.tape.copy()

  # Set up inductive prover.
  sim.step()  # Avoid applying rule immediately.
  #sim.prover = copy.copy(prover)
  # TODO(shawn): Don't add full rule, just one based on smaller exponents so
  # that we make sure induction applies.
  sim.prover.add_rule(rule)
  sim.prover.past_configs = None
  #sim.prover.verbose_prefix = sim.verbose_prefix + "  "

  end_config = rule.end_config()
  while sim.config() != end_config:  # or sim.loops > 100? (Failure condition)
    sim.step()

  # TODO(shawn): Do we need to find and prove the base case? Or do we just
  # expect that it was demonstrated by whatever asked us to prove this rule.

  return (sim.config() == end_config)
