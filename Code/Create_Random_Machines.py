#! /usr/bin/env python3
#
# Create_Random_Machines.py
#
"""
Generates some random Turing Machines for a given # of states and symbols.
"""

from optparse import OptionParser, OptionGroup
import random
import sys

import IO
import Turing_Machine

def random_machine(num_states, num_symbols):
  """Generate one random transition table with # of states and symbols."""
  # Although tm will not be in Tree Normal Form (TNF), it will have first cell
  # A0 -> 1RB.
  tm = Turing_Machine.Turing_Machine(num_states, num_symbols)

  # And one Halt state randomly chosen from all remaining cells.
  # Starts at 1 to avoid initial cell.
  halt_index = random.randrange(1, num_states * num_symbols)
  halt_state = halt_index // num_symbols
  halt_symbol = halt_index % num_symbols
  assert tm.is_cell_empty(halt_state, halt_symbol), (
      tm, halt_state, halt_symbol)
  tm.set_halt(halt_state, halt_symbol)

  # Randomly generate all other cells without regard for TNF.
  for state in range(num_states):
    for symbol in range(num_symbols):
      if tm.is_cell_empty(state, symbol):
        state_out = random.randrange(num_states)
        symbol_out = random.randrange(num_symbols)
        dir_out = random.randrange(2)
        tm.set_cell(state, symbol, state_out, symbol_out, dir_out)

  assert tm.num_empty_cells == 0, tm

  return tm

def write_random_records(io, num_states, num_symbols, num_machines):
  for _ in range(num_machines):
    record = IO.Record()
    record.ttable = random_machine(num_states, num_symbols).get_TTable()
    io.write_record(record)

def main(args):
  ## Parse command line options.
  usage = "usage: %prog --states= --symbols= --count= [options]"
  parser = OptionParser(usage=usage)
  req_parser = OptionGroup(parser, "Required Parameters")  # Oxymoron?
  req_parser.add_option("--states",  type=int, help="Number of states")
  req_parser.add_option("--symbols", type=int, help="Number of symbols")
  req_parser.add_option("--count", type=int,
                        help="Number of machines to generate")
  parser.add_option_group(req_parser)

  out_parser = OptionGroup(parser, "Output Options")
  out_parser.add_option("--outfile", dest="outfilename", metavar="OUTFILE",
                        default="-", help="Output file name - for stdout "
                        "[Default: %default]")
  parser.add_option_group(out_parser)

  (options, args) = parser.parse_args(args)

  ## Enforce required parameters
  if not options.states or not options.symbols or not options.count:
    parser.error("--states=, --symbols= and --count= are required parameters")

  if options.outfilename == "-":
    outfile = sys.stdout
  else:
    outfile = open(options.outfilename, "wb")

  io = IO.IO(None, outfile)

  write_random_records(io, options.states, options.symbols, options.count)


if __name__ == "__main__":
  main(sys.argv[1:])
