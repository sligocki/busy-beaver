#! /usr/bin/env python3
"""
Try Reverse_Engineer_Filter, CTL and then simulate TM as a Macro Machine using
the Proof System.
"""

import copy
import math
from optparse import OptionParser, OptionGroup
import sys
import time

import Alarm
from Common import Exit_Condition, GenContainer
import CTL1
import CTL2
import Halting_Lib
import IO
import Lin_Recur_Detect
from Macro import Turing_Machine, Simulator, Block_Finder
from Macro.Tape import INF
import Reverse_Engineer_Filter

import io_pb2


def add_option_group(parser):
  """Add Macro_Simulator options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)

  group = OptionGroup(parser, "Macro Simulator options")

  group.add_option("--max-loops", type=int, default=1000,
                   help="Max simulator loops to run each simulation (0 for infinite). "
                   "[Default: infinite]")
  group.add_option("--time", type=int, default=15,
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

  parser.add_option_group(group)

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)

def create_default_options():
  """Returns a set of default options."""
  parser = OptionParser()
  add_option_group(parser)
  options, args = parser.parse_args([])
  return options

def setup_CTL(machine, cutoff):
  options = create_default_options()
  options.prover = False
  sim = Simulator.Simulator(machine, options)
  sim.seek(cutoff)

  if sim.op_state != Turing_Machine.RUNNING:
    return False

  tape = [None, None]

  for d in range(2):
    tape[d] = [block.symbol for block in reversed(sim.tape.tape[d])
               if block.num != "Inf"]

  config = GenContainer(state=sim.state, dir=sim.dir, tape=tape)
  return config

def run_timer(ttable, options,
              tm_record : io_pb2.TMRecord,
              time_limit_sec : int):
  try:
    start_time = time.time()
    Alarm.ALARM.set_alarm(time_limit_sec)

    run_options(ttable, options, tm_record)
    Alarm.ALARM.cancel_alarm()

  except Alarm.AlarmException:
    Alarm.ALARM.cancel_alarm()
    tm_record.filter.simulator.ClearField("result")
    tm_record.filter.simulator.result.unknown_info.over_time.elapsed_time_sec = (
      time.time() - start_time)

def run_options(ttable, options,
                tm_record : io_pb2.TMRecord) -> None:
  """Run the Accelerated Turing Machine Simulator, running a few simple filters
  first and using intelligent blockfinding."""
  ## Test for quickly for infinite machine
  with IO.Timer(tm_record):
    if options.reverse_engineer:
      with IO.Timer(tm_record.filter.reverse_engineer):
        tm_record.filter.reverse_engineer.tested = True
        if Reverse_Engineer_Filter.test(ttable):
          tm_record.filter.reverse_engineer.success = True
          Halting_Lib.set_not_halting(tm_record.status, io_pb2.INF_REVERSE_ENGINEER)
          # Note: quasihalting result is not computable when using Reverse_Engineer filter.
          tm_record.status.quasihalt_status.is_decided = False
          return
        else:
          tm_record.filter.reverse_engineer.success = False

    if options.lin_steps:
      lr_info = tm_record.filter.lin_recur
      lr_info.parameters.max_steps = options.lin_steps
      lr_info.parameters.find_min_start_step = options.lin_min
      Lin_Recur_Detect.filter(ttable, lr_info, tm_record.status)
      if tm_record.status.halt_status.is_decided:
        # Return if halt status has been decided (either inf or halting).
        # LR filter is meant to detect halting, but it does run the TM for 100
        # steps or so, so it will detect many halting machines.
        return

    ## Construct the Macro Turing Machine (Backsymbol-k-Block-Macro-Machine)
    machine = Turing_Machine.make_machine(ttable)

    # If no explicit block-size given, use heuristics to find one.
    block_size = options.block_size
    if not block_size:
      if options.max_loops:
        bf_loops = options.max_loops // 100
      else:
        bf_loops = 100

      bf_info = tm_record.filter.block_finder
      bf_info.parameters.compression_search_loops = bf_loops
      bf_info.parameters.mult_sim_loops = bf_loops
      bf_info.parameters.extra_mult = options.bf_extra_mult
      Block_Finder.block_finder(machine, options,
                                bf_info.parameters, bf_info.result)
      block_size = bf_info.result.best_block_size

    # Do not create a 1-Block Macro-Machine (just use base machine)
    if block_size != 1:
      machine = Turing_Machine.Block_Macro_Machine(machine, block_size)
    if options.backsymbol:
      machine = Turing_Machine.Backsymbol_Macro_Machine(machine)

    if options.ctl:
      ctl_filter_info = tm_record.filter.ctl
      with IO.Timer(ctl_filter_info):
        if options.max_loops:
          ctl_init_step = options.max_loops // 10
        else:
          ctl_init_step = 1000

        CTL_config = setup_CTL(machine, ctl_init_step)

        # Run CTL filters unless machine halted
        if CTL_config:
          ctl_filter_info.init_step = ctl_init_step
          CTL_config_copy = copy.deepcopy(CTL_config)
          ctl_filter_info.ctl_as.tested = True
          if CTL1.CTL(machine, CTL_config_copy):
            ctl_filter_info.ctl_as.success = True
            Halting_Lib.set_not_halting(tm_record.status, io_pb2.INF_CTL)
            # Note: quasihalting result is not computed when using CTL filters.
            tm_record.status.quasihalt_status.is_decided = False
            return
          else:
            ctl_filter_info.ctl_as.success = False

          CTL_config_copy = copy.deepcopy(CTL_config)
          ctl_filter_info.ctl_as_b.tested = True
          if CTL2.CTL(machine, CTL_config_copy):
            ctl_filter_info.ctl_as_b.success = True
            Halting_Lib.set_not_halting(tm_record.status, io_pb2.INF_CTL)
            # Note: quasihalting result is not computed when using CTL filters.
            tm_record.status.quasihalt_status.is_decided = False
            return
          else:
            ctl_filter_info.ctl_as_b.success = False

    # Finally: Do the actual Macro Machine / Chain simulation.
    sim_info = tm_record.filter.simulator
    sim_info.parameters.block_size = block_size
    sim_info.parameters.has_blocksymbol_macro = options.backsymbol
    simulate_machine(machine, options, sim_info, tm_record.status)

def simulate_machine(machine : Turing_Machine.Turing_Machine,
                     options,
                     sim_info : io_pb2.SimulatorInfo,
                     bb_status : io_pb2.BBStatus) -> None:
  """Simulate a TM using the Macro Machine / Chain Simulator.
  Save the results into `sim_info`."""
  with IO.Timer(sim_info.result):
    sim_info.parameters.max_loops = options.max_loops
    sim_info.parameters.max_time_sec = options.time
    sim_info.parameters.max_tape_blocks = options.tape_limit
    sim_info.parameters.use_prover = options.prover
    sim_info.parameters.use_limited_rules = options.limited_rules
    sim_info.parameters.use_recursive_rules = options.recursive
    sim_info.parameters.use_collatz_rules = options.allow_collatz

    sim = Simulator.Simulator(machine, options)

    ## Run the simulator
    while ((sim_info.parameters.max_loops == 0 or
            sim.num_loops < sim_info.parameters.max_loops) and
           sim.op_state == Turing_Machine.RUNNING and
           sim.tape.compressed_size() <= sim_info.parameters.max_tape_blocks):
      sim.step()

    sim_info.result.num_loops = sim.num_loops
    sim_info.result.num_macro_moves = sim.num_macro_moves
    sim_info.result.num_chain_moves = sim.num_chain_moves
    sim_info.result.num_rule_moves = sim.num_rule_moves

    if sim.step_num > 0:
      sim_info.result.log10_num_steps = int(math.log10(sim.step_num))

    sim_info.result.num_rules_proven = sim.prover.rule_num - 1
    # TODO: add num_recursive_rules, num_collatz_rules, etc.
    sim_info.result.num_proofs_failed = sim.prover.num_failed_proofs

    # Various Unknown conditions
    if sim.tape.compressed_size() > sim_info.parameters.max_tape_blocks:
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
      raise Exception(sim.op_state, ttable, sim)


if __name__ == "__main__":
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  add_option_group(parser)
  (options, args) = parser.parse_args()


  if len(args) < 1:
    parser.error("Must have at least one argument, machine_file")
  filename = args[0]

  if len(args) >= 2:
    try:
      line = int(args[1])
    except ValueError:
      parser.error("line_number must be an integer.")
    if line < 1:
      parser.error("line_number must be >= 1")
  else:
    line = 1

  ttable = IO.load_TTable_filename(filename, line)

  if options.time > 0:
    print(run_timer(ttable, options, None, options.time))
  else:
    print(run_options(ttable, options))
