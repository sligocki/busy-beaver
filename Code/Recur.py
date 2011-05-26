#! /usr/bin/env python

import sys, string, copy, numpy

from Macro import Turing_Machine, Simulator, Block_Finder
import IO
import Output_Machine

# White, Red, Blue, Green, Magenta, Cyan, Brown/Yellow
color = [49, 41, 44, 42, 45, 46, 43]
# Characters to use for states (end in "Z" so that halt is Z)
states = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*" + "Z"
symbols = string.digits + "-"
dirs = "LRS-"

def print_machine(machine):
  """
  Pretty-print the contents of the Turing machine.
  This method prints the state transition information
  (number to print, direction to move, next state) for each state
  but not the contents of the tape.
  """

  sys.stdout.write("\n")
  sys.stdout.write("Transition table:\n")
  sys.stdout.write("\n")

  TTable = machine.trans_table

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  sys.stdout.write("       ")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("|  %d  " % j)
  sys.stdout.write("|\n")

  sys.stdout.write("   +---")
  for j in xrange(len(TTable[0])):
    sys.stdout.write("+-----")
  sys.stdout.write("+\n")

  for i in xrange(len(TTable)):
    sys.stdout.write("   | %c " % states[i])
    for j in xrange(len(TTable[i])):
      sys.stdout.write("| ")
      if TTable[i][j][0] == -1 and \
         TTable[i][j][1] == -1 and \
         TTable[i][j][2] == -1:
        sys.stdout.write("--- ")
      else:
        sys.stdout.write("%c"   % symbols[TTable[i][j][0]])
        sys.stdout.write("%c"   % dirs   [TTable[i][j][1]])
        sys.stdout.write("%c "  % states [TTable[i][j][2]])
    sys.stdout.write("|\n")

    sys.stdout.write("   +---")
    for j in xrange(len(TTable[0])):
      sys.stdout.write("+-----")
    sys.stdout.write("+\n")

  sys.stdout.write("\n\n")

  sys.stdout.flush()


def stripped_info(block):
  """Get an abstraction of a tape block. We try to prove rules between
  configuration which have the same abstraction.
  """
  #if block.num == 1:
  #  return block.symbol, 1
  #else:
  return block.symbol

def strip_config(state, dir, tape):
  """"Return a generalized configuration removing the non-1 repetition counts from the tape."""
  # Optimization: Strip off Infinity blocks before we run the map (see tape[x][1:]).
  # Turns out Infinity.__cmp__ is expensive when run millions of times.
  # It used to spend up to 25% of time here.
  # TODO: This map is expensive upwards of 10% of time is spend here.
  return (tuple(map(stripped_info, tape[0])),
          state, dir,
          tuple(reversed(map(stripped_info, tape[1]))))


def run(TTable, block_size, back, prover, recursive, options):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.make_machine(TTable)

  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    block_size = Block_Finder.block_finder(m, options)

  #if not options.quiet:
  #  print_machine(m)

  # Do not create a 1-Block Macro-Machine (just use base machine)
  if block_size != 1:
    m = Turing_Machine.Block_Macro_Machine(m, block_size)
  if back:
    m = Turing_Machine.Backsymbol_Macro_Machine(m)

  global sim  # For debugging, especially with --manual
  sim = Simulator.Simulator(m, options)

  if options.manual:
    return  # Let's us run the machine manually. Must be run as python -i Quick_Sim.py

  groups = {}

  total_loops = 0;

  while (sim.op_state == Turing_Machine.RUNNING and
         (options.loops == 0 or total_loops < options.loops)):
    # print "%10d" % sim.step_num,"  ",sim.tape.print_with_state(sim.state)

    sim.step()

    if len(sim.tape.tape[0]) == 1 or len(sim.tape.tape[1]) == 1:
      min_config = strip_config(sim.state,sim.dir,sim.tape.tape)

      if min_config in groups:
        groups[min_config].append([copy.deepcopy(sim.tape.tape[0][1:]),
                                   copy.deepcopy(sim.tape.tape[1][1:]),
                                   sim.step_num])
      else:
        groups[min_config] = [[copy.deepcopy(sim.tape.tape[0][1:]),
                               copy.deepcopy(sim.tape.tape[1][1:]),
                               sim.step_num],]

    total_loops += 1;

  #print "%10d" % sim.step_num,"  ",sim.tape.print_with_state(sim.state)
  #print

  sorted_keys = sorted(groups,key=lambda item: len(item[0])+len(item[3]))

  for min_config in sorted_keys:
    group = groups[min_config]

    if len(group) >= 4:
      print Output_Machine.display_ttable(TTable),"  ",
      print "%5d" % len(group),"  ",
      print "(%5d)" % len(groups),"  ",
      print min_config

      growth = [[] for i in xrange(len(group[0][0]) + len(group[0][1]) + 1)]
      for config in group:
        index = 0
        for symbol in config[0]:
          growth[index].append(symbol.num)
          index += 1
        for symbol in config[1]:
          growth[index].append(symbol.num)
          index += 1
        growth[index].append(config[2])

      recur_all = True

      for series in growth:
        series = [term for term in series if term < 100000000]
        if len(series) > 20:
          series = series[len(series)-20:]

        print "     ",series

        recur_this = False

        for n in xrange(0,len(series)/2):
          a = [[1,] for i in xrange(len(series)-n)]
          for m in xrange(0,n):
            for i in xrange(len(series)-n):
              a[i].append(series[m+i])

          b = [[series[i],] for i in xrange(n,len(series))]

          A = numpy.array(a)
          B = numpy.array(b)

          [x,residue,rank,sv] = numpy.linalg.lstsq(A,B)
          if len(residue) > 0:
            residue = residue[0]

          print "        ",n,residue,

          if residue:
            if residue < 1e-12:
              int_coefs = [int(round(coef[0])) for coef in x]
              int_coefs.reverse()

              constant = int_coefs[-1]
              int_coefs = int_coefs[:-1]

              if not int_coefs or int_coefs[-1] != 0:
                print "success",

                print " F(n) =",

                first = True
                for i in xrange(len(int_coefs)):
                  if first:
                    if int_coefs[i] != 0:
                      first = False
                      if int_coefs[i] > 0:
                        if int_coefs[i] == 1:
                          print "F(n-%d)" % (i+1,),
                        else:
                          print int_coefs[i],"F(n-%d)" % (i+1,),
                      else:
                        if int_coefs[i] == -1:
                          print "-F(n-%d)" % (i+1,),
                        else:
                          print int_coefs[i],"F(n-%d)" % (i+1,),
                  else:
                    if int_coefs[i] != 0:
                      if int_coefs[i] > 0:
                        if int_coefs[i] == 1:
                          print "+","F(n-%d)" % (i+1,),
                        else:
                          print "+",int_coefs[i],"F(n-%d)" % (i+1,),
                      else:
                        if int_coefs[i] == -1:
                          print "-","F(n-%d)" % (i+1,),
                        else:
                          print "-",-int_coefs[i],"F(n-%d)" % (i+1,),

                if len(int_coefs) > 0:
                  if constant > 0:
                    print "+",
                  elif constant < 0:
                    print "-",

                if constant > 0:
                  print constant
                elif constant < 0:
                  print -constant

                recur_this = True
                break
              else:
                print "failure",

                int_coefs = [coef[0] for coef in x]
                int_coefs.reverse()

                constant = int_coefs[-1]
                int_coefs = int_coefs[:-1]

                print " F(n) =",

                first = True
                for i in xrange(len(int_coefs)):
                  if first:
                    if int_coefs[i] != 0.0:
                      first = False
                      if int_coefs[i] > 0.0:
                        if int_coefs[i] == 1.0:
                          print "F(n-%d)" % (i+1,),
                        else:
                          print "%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                      else:
                        if int_coefs[i] == -1.0:
                          print "-F(n-%d)" % (i+1,),
                        else:
                          print "%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                  else:
                    if int_coefs[i] != 0.0:
                      if int_coefs[i] > 0.0:
                        if int_coefs[i] == 1.0:
                          print "+","F(n-%d)" % (i+1,),
                        else:
                          print "+","%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                      else:
                        if int_coefs[i] == -1.0:
                          print "-","F(n-%d)" % (i+1,),
                        else:
                          print "-","%.3f" % -int_coefs[i],"F(n-%d)" % (i+1,),

                if len(int_coefs) > 0.0:
                  if constant > 0.0:
                    print "+",
                  elif constant < 0.0:
                    print "-",

                if constant > 0.0:
                  print "%.3f" % constant
                elif constant < 0.0:
                  print "%.3f" % -constant

                break
            else:
              print "failure",

              int_coefs = [coef[0] for coef in x]
              int_coefs.reverse()

              constant = int_coefs[-1]
              int_coefs = int_coefs[:-1]

              print " F(n) =",

              first = True
              for i in xrange(len(int_coefs)):
                if first:
                  if int_coefs[i] != 0.0:
                    first = False
                    if int_coefs[i] > 0.0:
                      if int_coefs[i] == 1.0:
                        print "F(n-%d)" % (i+1,),
                      else:
                        print "%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                    else:
                      if int_coefs[i] == -1.0:
                        print "-F(n-%d)" % (i+1,),
                      else:
                        print "%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                else:
                  if int_coefs[i] != 0.0:
                    if int_coefs[i] > 0.0:
                      if int_coefs[i] == 1.0:
                        print "+","F(n-%d)" % (i+1,),
                      else:
                        print "+","%.3f" % int_coefs[i],"F(n-%d)" % (i+1,),
                    else:
                      if int_coefs[i] == -1.0:
                        print "-","F(n-%d)" % (i+1,),
                      else:
                        print "-","%.3f" % -int_coefs[i],"F(n-%d)" % (i+1,),

              if len(int_coefs) > 0.0:
                if constant > 0.0:
                  print "+",
                elif constant < 0.0:
                  print "-",

              if constant > 0.0:
                print "%.3f" % constant
              elif constant < 0.0:
                print "%.3f" % -constant
          else:
            print

        recur_all = recur_all and recur_this
        print

      # for elem in group:
      #   print elem
      print "     ",recur_all
      print

      break


if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup

  from Option_Parser import open_infile

  # Parse command line options.
  usage = "usage: %prog [options] machine_file"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  # TODO: Combine optparsers from MacroMachine, Enumerate and here.
  parser.add_option("-q", "--quiet", action="store_true", help="Brief output")
  parser.add_option("-v", "--verbose", action="store_true",
                    help="Print step-by-step informaion from simulator "
                    "and prover (Overrides other --verbose-* flags).")
  parser.add_option("-l", "--loops", type=int, default=1000,
                    help="Specify a maximum number of loops [Default %default].")
  parser.add_option("--print-loops", type=int, default=10000, metavar="LOOPS",
                    help="Print every LOOPS loops [Default %default].")
  
  parser.add_option("--manual", action="store_true",
                    help="Don't run any simulation, just set up simulator "
                    "and quit. (Run as python -i Quick_Sim.py to interactively "
                    "run simulation.)")

  Simulator.add_option_group(parser)
  Block_Finder.add_option_group(parser)
  
  (options, args) = parser.parse_args()

  if options.quiet:
    options.verbose_simulator = False
    options.verbose_prover = False
    options.verbose_block_finder = False
  elif options.verbose:
    options.verbose_simulator = True
    options.verbose_prover = True
    options.verbose_block_finder = True
  
  if len(args) < 1:
    parser.error("Must have one argument, machine_file")
  infilename = args[0]

  infile = open_infile(infilename)
  
  # if len(args) >= 2:
  #   try:
  #     line = int(args[1])
  #   except ValueError:
  #     parser.error("line_number must be an integer.")
  #   if line < 1:
  #     parser.error("line_number must be >= 1")
  # else:
  #   line = 1
  
  io = IO.IO(infile, None, None)

  for io_record in io:
    ttable = io_record.ttable
    
    run(ttable, options.block_size, options.backsymbol, options.prover, 
                options.recursive, options)
