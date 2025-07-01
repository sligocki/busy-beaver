#! /usr/bin/env python3
"""
Try Reverse_Engineer_Filter, CTL and then simulate TM as a Macro Machine using
the Proof System.
"""

import math
from optparse import OptionParser, OptionGroup
import time

import CTL_Filter
import Halting_Lib
import IO
from IO import TM_Record
import Lin_Recur_Detect
from Macro import Turing_Machine, Simulator, Block_Finder
import Reverse_Engineer_Filter

import io_pb2


def add_option_group(parser):
  """Add Macro_Simulator options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Macro Simulator options")

  group.add_option("--max-loops", type=int, default=1000,
                   help="Max simulator loops to run each simulation (0 for infinite). "
                   "[Default: infinite]")
  group.add_option("--time", type=float, default=15.0,
                   help="Max seconds to run each simulation. "
                   "[Default: %default]")
  group.add_option("--tape-limit", type=int, default=50,
                   help="Max tape size to allow.")
  group.add_option("--lin-steps", type=int, default=127,
                   help="Number of steps to run Lin_Recur detection (0 means skip).")
  group.add_option("--lin-min", action="store_true", default=False)
  group.add_option("--no-reverse-engineer", dest="reverse_engineer",
                   action="store_false", default=True,
                   help="Don't try Reverse_Engineer_Filter.")
  group.add_option("--no-ctl", dest="ctl", action="store_false", default=True,
                   help="Don't try CTL optimization.")
  group.add_option("--no-sim", dest="run_sim", action="store_false", default=True,
                   help="Don't even run Macro/Simulator (ex: only run Lin_Recur).")

  parser.add_option_group(group)

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)

def run_options(tm_record : TM_Record,
                options,
                time_limit_sec : float) -> None:
  """Run the Accelerated Turing Machine Simulator, running a few simple filters
  first and using intelligent blockfinding."""
  base_tm = tm_record.tm()
  ## Test for quickly for infinite machine
  with IO.Timer(tm_record.proto):
    if options.reverse_engineer:
      with IO.Timer(tm_record.proto.filter.reverse_engineer):
        tm_record.proto.filter.reverse_engineer.tested = True
        if Reverse_Engineer_Filter.is_infinite(base_tm):
          tm_record.proto.filter.reverse_engineer.success = True
          Halting_Lib.set_not_halting(tm_record.proto.status, io_pb2.INF_REVERSE_ENGINEER)
          # Note: quasihalting result is not computable when using Reverse_Engineer filter.
          tm_record.proto.status.quasihalt_status.is_decided = False
          return
        else:
          tm_record.proto.filter.reverse_engineer.success = False

    if options.lin_steps:
      lr_info = tm_record.proto.filter.lin_recur
      lr_info.parameters.max_steps = options.lin_steps
      lr_info.parameters.find_min_start_step = options.lin_min
      Lin_Recur_Detect.filter(base_tm, lr_info, tm_record.proto.status)
      if tm_record.proto.status.halt_status.is_decided:
        # Return if halt status has been decided (either inf or halting).
        # LR filter is meant to detect halting, but it does run the TM for 100
        # steps or so, so it will detect many halting machines.
        return

    if options.run_sim:
      # If no explicit block-size given, use heuristics to find one.
      block_size = options.block_size
      if not block_size:
        if options.max_loops:
          bf_loops = options.max_loops // 100
        else:
          bf_loops = 100

        bf_info = tm_record.proto.filter.block_finder
        bf_info.parameters.compression_search_loops = bf_loops
        bf_info.parameters.mult_sim_loops = bf_loops
        bf_info.parameters.max_block_mult = options.max_block_mult
        bf_info.parameters.block_mult = options.block_mult
        bf_info.parameters.max_block_size = options.max_block_size
        Block_Finder.block_finder(base_tm, options,
                                  bf_info.parameters, bf_info.result)
        block_size = bf_info.result.best_block_size

      machine = base_tm
      # Do not create a 1-Block Macro-Machine (just use base machine)
      if block_size != 1:
        machine = Turing_Machine.Block_Macro_Machine(machine, block_size)
      if options.backsymbol:
        machine = Turing_Machine.Backsymbol_Macro_Machine(machine)

      if options.ctl:
        if options.max_loops:
          ctl_init_step = options.max_loops // 10
        else:
          ctl_init_step = 1000

        if CTL_Filter.filter(tm_record, "CTL2", block_size, offset=0,
                             max_time=options.time, cutoff=ctl_init_step,
                             use_backsymbol=True):
          return

      # Finally: Do the actual Macro Machine / Chain simulation.
      sim_info = tm_record.proto.filter.simulator
      sim_info.parameters.block_size = block_size
      sim_info.parameters.has_blocksymbol_macro = options.backsymbol
      simulate_machine(machine, options, sim_info, tm_record.proto.status, time_limit_sec)

def simulate_machine(machine : Turing_Machine.Turing_Machine,
                     options,
                     sim_info : io_pb2.SimulatorInfo,
                     bb_status : io_pb2.BBStatus,
                     time_limit_sec : float) -> None:
  """Simulate a TM using the Macro Machine / Chain Simulator.
  Save the results into `sim_info`."""
  with IO.Timer(sim_info.result):
    sim_info.parameters.max_loops = options.max_loops
    sim_info.parameters.max_time_sec = options.time
    sim_info.parameters.max_tape_blocks = options.tape_limit
    sim_info.parameters.use_prover = options.prover
    sim_info.parameters.use_limited_rules = options.limited_rules
    sim_info.parameters.use_recursive_rules = options.recursive

    # TODO: For now, we can't compute steps when evaluating Linear_Rules
    if options.exp_linear_rules:
      options.compute_steps = False
    sim = Simulator.Simulator(machine, options)

    ## Run the simulator
    try:
      start_time = time.time()
      timeout = False

      while ((sim_info.parameters.max_loops == 0 or
              sim.num_loops < sim_info.parameters.max_loops) and
             sim.op_state == Turing_Machine.RUNNING and
             sim.tape.compressed_size() <= sim_info.parameters.max_tape_blocks):
        sim.step()
        if time_limit_sec > 0:
          if time.time() - start_time >= time_limit_sec:
            timeout = True
            break

    finally:
      # Set these stats even if timeout (exception) is raised.
      sim_info.result.num_loops = sim.num_loops
      sim_info.result.num_macro_moves = sim.num_macro_moves
      sim_info.result.num_chain_moves = sim.num_chain_moves
      sim_info.result.num_rule_moves = sim.num_rule_moves

      if sim.step_num > 0:
        sim_info.result.log10_num_steps = int(math.log10(sim.step_num))

      sim_info.result.num_rules_proven = sim.prover.num_rules
      sim_info.result.num_meta_diff_rules_proven = sim.prover.num_meta_diff_rules
      sim_info.result.num_linear_rules_proven = sim.prover.num_linear_rules
      sim_info.result.num_finite_linear_rules_proven = sim.prover.num_finite_linear_rules
      sim_info.result.num_exponential_rules_proven = sim.prover.num_exponential_rules
      sim_info.result.num_gen_rules_proven = sim.prover.num_gen_rules
      sim_info.result.num_collatz_rules = sim.prover.num_collatz_rules
      sim_info.result.num_proofs_failed = sim.prover.num_failed_proofs

    # Various Unknown conditions
    if timeout:
      sim_info.result.unknown_info.over_time.elapsed_time_sec = time.time() - start_time

    elif sim.tape.compressed_size() > sim_info.parameters.max_tape_blocks:
      sim_info.result.unknown_info.over_tape.compressed_tape_size = sim.tape.compressed_size()

    elif sim.op_state == Turing_Machine.RUNNING:
      sim_info.result.unknown_info.over_loops.num_loops = sim.num_loops

    # TODO: Stop calling this "GAVE_UP" if we're only using it for one failure type.
    elif sim.op_state == Turing_Machine.GAVE_UP:
      over_steps_in_macro_info = sim_info.result.unknown_info.over_steps_in_macro
      over_steps_in_macro_info.macro_symbol = str(sim.tape.get_top_symbol())
      over_steps_in_macro_info.macro_state = str(sim.state)
      over_steps_in_macro_info.macro_dir_is_right = (sim.dir == Turing_Machine.RIGHT)

    elif sim.op_state == Turing_Machine.INF_REPEAT:
      Halting_Lib.set_not_halting(bb_status, sim.inf_reason)

      if sim.states_last_seen is None:
        bb_status.quasihalt_status.is_decided = False
      else:
        Halting_Lib.set_inf_recur(bb_status,
                                  states_to_ignore=sim.inf_recur_states,
                                  states_last_seen=sim.states_last_seen)

      inf_info = sim_info.result.infinite_info
      if sim.inf_reason == io_pb2.INF_MACRO_STEP:
        inf_info.macro_repeat.macro_symbol = str(sim.tape.get_top_symbol())
        inf_info.macro_repeat.macro_state = str(sim.state)
        inf_info.macro_repeat.macro_dir_is_right = (sim.dir == Turing_Machine.RIGHT)

      elif sim.inf_reason == io_pb2.INF_CHAIN_STEP:
        inf_info.chain_move.macro_state = str(sim.state)
        inf_info.chain_move.dir_is_right = (sim.dir == Turing_Machine.RIGHT)

      elif sim.inf_reason == io_pb2.INF_PROOF_SYSTEM:
        # TODO(shawn): Actually list rule here somehow.
        inf_info.proof_system.rule = "?"

      else:
        raise Exception(sim.inf_reason)

    elif sim.op_state in (Turing_Machine.UNDEFINED, Turing_Machine.HALT):
      # TM Halting and reaching UNDEFINED are treated the same here.
      # For enumeration, TMs never have halt transition when run, so we
      # will always hit the UNDEFINED case, but then treat it like a halt.
      from_symbol, from_state = sim.op_details[0][:2]
      halt_info = sim_info.result.halt_info.is_halting = True
      Halting_Lib.set_halting(bb_status,
                              halt_steps = sim.step_num,
                              halt_score = sim.get_nonzeros(),
                              from_state = from_state,
                              from_symbol = from_symbol)

    else:
      raise Exception(sim.op_state, tm.ttable_str(), sim)
