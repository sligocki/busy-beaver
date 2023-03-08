#! /usr/bin/env python3
"""
A TM simulator with a variety of advanced features, options, and output
formats.
"""

from pathlib import Path
import string
import sys

from Macro import Turing_Machine, Simulator, Block_Finder
import Halting_Lib
import IO

import io_pb2

def run(machine, block_size, back, prover, recursive, options):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)

  # If no explicit block-size given, use heuristics to find one.
  if not block_size:
    bf_info = io_pb2.BlockFinderInfo()
    bf_info.parameters.compression_search_loops = options.bf_loops
    bf_info.parameters.mult_sim_loops = options.bf_loops
    bf_info.parameters.extra_mult = options.bf_extra_mult
    bf_info.parameters.max_block_size = 0  # No max for Quick_Sim
    Block_Finder.block_finder(machine, options,
                              bf_info.parameters, bf_info.result)
    block_size = bf_info.result.best_block_size

  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    machine = Turing_Machine.Block_Macro_Machine(
      machine, block_size,
      max_sim_steps_per_symbol=options.max_steps_in_block)
  if back:
    machine = Turing_Machine.Backsymbol_Macro_Machine(machine,
      max_sim_steps_per_symbol=options.max_steps_in_backsymbol)

  global sim  # For debugging, especially with --manual
  sim = Simulator.Simulator(machine, options)

  if options.manual:
    return  # Let's us run the machine manually. Must be run as python -i Quick_Sim.py
  try:
    if options.quiet or options.verbose:  # Note verbose prints inside sim.step()
      if options.verbose:
        sim.verbose_print()

      total_loops = 0;

      while (sim.op_state == Turing_Machine.RUNNING and
             (options.max_loops == 0 or total_loops < options.max_loops)):
        sim.step()
        total_loops += 1;
    else:
      # TODO: maybe print based on time
      total_loops = 0;

      while (sim.op_state == Turing_Machine.RUNNING and
             (options.max_loops == 0 or total_loops < options.max_loops)):
        sim.print_self()
        sim.loop_run(options.print_loops)
        total_loops += options.print_loops;
  finally:
    sim.print_self()

  if sim.op_state == Turing_Machine.HALT:
    print()
    print("Turing Machine Halted")
    print()
    if options.compute_steps:
      print("Steps:   ", sim.step_num)
    print("Nonzeros:", sim.get_nonzeros())
    print()
  elif sim.op_state == Turing_Machine.INF_REPEAT:
    bb_status = io_pb2.BBStatus()
    Halting_Lib.set_inf_recur(bb_status,
                              states_to_ignore=sim.inf_recur_states,
                              states_last_seen=sim.states_last_seen)
    print()
    print("Turing Machine proven Infinite")
    print("Reason:", io_pb2.InfReason.Name(sim.inf_reason))
    print("Quasihalt:")
    print(bb_status.quasihalt_status)
  elif sim.op_state == Turing_Machine.UNDEFINED:
    print()
    print("Turing Machine reached Undefined transition")
    print("State: ", sim.op_details[0][1])
    print("Symbol:", sim.op_details[0][0])
    print()
    if options.compute_steps:
      print("Steps:   ", sim.step_num)
    print("Nonzeros:", sim.get_nonzeros())
    print()
  elif sim.op_state == Turing_Machine.GAVE_UP:
    print()
    print("Gave up while simulating Turing Machine")
    print("Info:", sim.op_details)
  else:
    print()
    print("Unexpected sim exit condition:", sim.op_state, sim.op_details)

  if options.print_macro_ttable and isinstance(machine, Turing_Machine.Macro_Machine):
    macro_states = set()
    macro_symbols = set()
    for (macro_symbol_in, macro_state_in, macro_dir_in) in machine.trans_table.keys():
      macro_states.add( (macro_state_in, macro_dir_in) )
      macro_symbols.add(macro_symbol_in)

    macro_states = sorted(macro_states)
    macro_symbols = sorted(macro_symbols)
    table = [["" for _ in range(len(macro_symbols) + 1)]
             for _ in range(len(macro_states) + 1)]
    for y, macro_symbol in enumerate(macro_symbols):
      table[0][y+1] = str(macro_symbol)
    for x, (macro_state, dir) in enumerate(macro_states):
      state_dir_str = macro_state.print_with_dir(dir)
      if dir == Turing_Machine.RIGHT:
        table[x+1][0] = " %s>" % (state_dir_str,)
      else:
        assert dir == Turing_Machine.LEFT, dir
        table[x+1][0] = "<%s " % (state_dir_str,)

    num_trans = 0
    for x, (macro_state_in, dir_in) in enumerate(macro_states):
      for y, macro_symbol_in in enumerate(macro_symbols):
        if (macro_symbol_in, macro_state_in, dir_in) in machine.trans_table:
          trans = machine.trans_table[(macro_symbol_in, macro_state_in, dir_in)]
          state_dir_out_str = trans.state_out.print_with_dir(trans.dir_out)
          if trans.dir_out == Turing_Machine.RIGHT:
            table[x+1][y+1] = "%s %s>" % (trans.symbol_out, state_dir_out_str)
          else:
            assert trans.dir_out == Turing_Machine.LEFT, trans
            table[x+1][y+1] = "<%s %s" % (state_dir_out_str, trans.symbol_out)
          num_trans += 1

    print()
    print("Macro Machine TTable (%d states, %d symbols, %d transitions):" % (
      len(macro_states), len(macro_symbols), num_trans))
    print(table_to_str(table))

def table_to_str(table):
  max_cell_width = max(max(len(cell) for cell in row) for row in table)
  cell_width = max_cell_width + 2

  t_str = ""
  for row in table:
    for cell in row:
      t_str += "| %*s " % (cell_width, cell)
    t_str += "|\n"

  return t_str


if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  # TODO: Combine optparsers from MacroMachine, Enumerate and here.
  parser.add_option("-q", "--quiet", action="store_true", help="Brief output")
  parser.add_option("-v", "--verbose", action="store_true",
                    help="Print step-by-step informaion from simulator "
                    "and prover (Overrides other --verbose-* flags).")

  parser.add_option("--max-loops", type=int, default=0,
                    help="Specify a maximum number of loops.")
  parser.add_option("--bf-loops", type=int, default=10_000,
                    help="Number of steps to run Block Finder.")

  parser.add_option("--max-steps-in-block", type=int, default=1_000_000)
  parser.add_option("--max-steps-in-backsymbol", type=int, default=1_000)

  parser.add_option("--print-loops", type=int, default=10_000, metavar="LOOPS",
                    help="Print every LOOPS loops [Default %default].")
  parser.add_option("--print-macro-ttable", action="store_true")

  parser.add_option("--manual", action="store_true",
                    help="Don't run any simulation, just set up simulator "
                    "and quit. (Run as python -i Quick_Sim.py to interactively "
                    "run simulation.)")

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)

  (options, args) = parser.parse_args()

  options.verbose_block_finder = True
  if options.quiet:
    options.verbose_simulator = False
    options.verbose_prover = False
  elif options.verbose:
    options.verbose_simulator = True
    options.verbose_prover = True

  if options.max_loops and options.print_loops > options.max_loops:
    options.print_loops = options.max_loops

  if len(args) < 1:
    parser.error("Must have at least one argument, machine_file")
  filename = Path(args[0])

  if len(args) >= 2:
    try:
      record_num = int(args[1])
    except ValueError:
      parser.error("record_num must be an integer.")
  else:
    record_num = 0

  machine = IO.load_tm(filename, record_num)
  if not options.quiet:
    print(Turing_Machine.machine_ttable_to_str(machine))

  run(machine, options.block_size, options.backsymbol, options.prover,
               options.recursive, options)
