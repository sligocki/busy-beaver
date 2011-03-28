#! /usr/bin/env python

import sys, string

from Macro import Turing_Machine, Simulator, Block_Finder, Tape
import IO

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


import os
import cmd
import rlcompleter
import readline

readline.parse_and_bind ("bind ^I rl_complete")

class BBConsole(cmd.Cmd):

  def __init__(self, TTable, options):
    cmd.Cmd.__init__(self)
    self.cmdnum = 1
    self.prompt = "%d> " % (self.cmdnum,)

    self.TTable = TTable

    self.sim_options = options

    # Construct Machine (Backsymbol-k-Block-Macro-Machine)
    m = Turing_Machine.make_machine(self.TTable)

    if not self.sim_options.quiet:
      print_machine(m)

    # If no explicit block-size given set it to 1
    if not self.sim_options.block_size:
      self.sim_options.block_size = 1

    # Do not create a 1-Block Macro-Machine (just use base machine)
    if self.sim_options.block_size != 1:
      m = Turing_Machine.Block_Macro_Machine(m, self.sim_options.block_size)
    if self.sim_options.backsymbol:
      m = Turing_Machine.Backsymbol_Macro_Machine(m)

    self.sim = Simulator.Simulator(m, self.sim_options.recursive,
                                      enable_prover=self.sim_options.prover,
                                      init_tape=True,
                                      compute_steps=self.sim_options.compute_steps,
                                      verbose_simulator=self.sim_options.verbose_simulator,
                                      verbose_prover=self.sim_options.verbose_prover,
                                      verbose_prefix="")

    print "Welcome to the machine!\n"

    self.sim.verbose_print()

  ## Command definitions ##
  def do_EOF(self, args):
    """Exit on system end of file character"""
    print
    return self.do_exit(args)

  def do_exit(self, args):
    """Exits from the console"""
    print
    return -1

  def do_help(self, args):
    """Get help on commands
       'help' or '?' with no arguments prints a list of commands for which help is available
       'help <command>' or '? <command>' gives help on <command>
    """
    ## The only reason to define this method is for the help text in the doc string
    cmd.Cmd.do_help(self, args)

  def do_hist(self, args):
    """Print a list of commands that have been entered"""
    num = 1
    com_prev = ""
    for com in self._hist:
      if com != "" and com != com_prev:
        print "%4d  %s" % (num,com)
        com_prev = com
      num += 1

  def do_quit(self, args):
    """Exits from the console"""
    return self.do_exit(args)

  def do_step(self,args):
    """Take on step of the current machine"""
    self.sim.step()

    if self.sim.op_state == Turing_Machine.HALT:
      print
      print "Turing Machine Halted!"
      print
      if options.compute_steps:
        print "Steps:   ", self.sim.step_num
      print "Nonzeros:", self.sim.get_nonzeros()
      print
    elif self.sim.op_state == Turing_Machine.INF_REPEAT:
      print
      print "Turing Machine proven Infinite!"
      print "Reason:", self.sim.inf_reason
    elif self.sim.op_state == Turing_Machine.UNDEFINED:
      print
      print "Turing Machine reached Undefined transition!"
      print "State: ", self.sim.op_details[0][1]
      print "Symbol:", self.sim.op_details[0][0]
      print
      if options.compute_steps:
        print "Steps:   ", self.sim.step_num
      print "Nonzeros:", self.sim.get_nonzeros()
      print

  def do_tape(self, args):
    self.stdout.write("\n")
    self.stdout.write("   Tape: ")
    self.stdout.flush()

    tape_state_string = self.stdin.readline()

    tape_state_tokens = tape_state_string.split()

    tape_parse = [tape_state_token.split("^") for tape_state_token in tape_state_tokens]

    tape_length = 0

    state_index = -1
    back_index = -1

    token_length = len(tape_parse)
    symbol_length = len(tape_parse[0][0])

    for i in xrange(token_length):
      token = tape_parse[i]
      if len(token) == 2:
        tape_length += 1
        if len(token[0]) != symbol_length:
          print "Tape symbol lengths don't match"
          return
        if symbol_length == 1:
          new_symbol = int(token[0])
        else:
          new_symbol = Turing_Machine.Block_Symbol([int(c) for c in token[0]])
        token[0] = new_symbol
      elif token[0][0] == "(":
        if len(token[0]) != symbol_length + 2:
          print "Back symbol length doesn't match tape symbol length"
          return
        back_index = i
      elif token[0][0] == "<":
        state_index = i
        tape_dir = 0
      elif token[0][-1] == ">":
        state_index = i
        tape_dir = 1
      else:
        print "Unrecognized tape entry: %s" % (token,)
        return

    if back_index > -1:
      if tape_dir == 0:
        if state_index > back_index:
          print "State and backsymbol are out of order"
          return
        elif state_index + 1 != back_index:
          print "State and backsymbol aren't together"
          return
      else:
        if state_index < back_index:
          print "State and backsymbol are out of order"
          return
        elif state_index - 1 != back_index:
          print "State and backsymbol aren't together"
          return
      new_back_symbol = tape_parse[back_index][0][1:-1]
    else:
      new_back_symbol = ""
    
    if tape_dir == 0:
      new_state = tape_parse[state_index][0][1]
    else:
      new_state = tape_parse[state_index][0][0]
        
    new_tape = Tape.Chain_Tape()
    new_tape.dir = tape_dir

    new_tape.tape = [[], []]
    for i in xrange(token_length):
      if i < state_index and (back_index == -1 or i < back_index):
        if tape_parse[i][1] == "Inf":
          new_tape.tape[0].append(Tape.Repeated_Symbol(tape_parse[i][0],Tape.INF))
        else:
          new_tape.tape[0].append(Tape.Repeated_Symbol(tape_parse[i][0],int(tape_parse[i][1])))
      if i > state_index and (back_index == -1 or i > back_index):
        if tape_parse[i][1] == "Inf":
          new_tape.tape[1].append(Tape.Repeated_Symbol(tape_parse[i][0],Tape.INF))
        else:
          new_tape.tape[1].append(Tape.Repeated_Symbol(tape_parse[i][0],int(tape_parse[i][1])))

    new_tape.tape[1].reverse()
    new_tape.displace = 0

    self.sim_options.block_size = symbol_length

    if back_index >= 0:
      self.sim_options.backsymbol = True
    else:
      self.sim_options.backsymbol = False

    # Construct Machine (Backsymbol-k-Block-Macro-Machine)
    m = Turing_Machine.make_machine(self.TTable)

    # If no explicit block-size given set it to 1
    if not self.sim_options.block_size:
      self.sim_options.block_size = 1

    # Do not create a 1-Block Macro-Machine (just use base machine)
    if self.sim_options.block_size != 1:
      m = Turing_Machine.Block_Macro_Machine(m, self.sim_options.block_size)
    if self.sim_options.backsymbol:
      m = Turing_Machine.Backsymbol_Macro_Machine(m)

    self.sim = Simulator.Simulator(m, self.sim_options.recursive,
                                      enable_prover=self.sim_options.prover,
                                      init_tape=True,
                                      compute_steps=self.sim_options.compute_steps,
                                      verbose_simulator=self.sim_options.verbose_simulator,
                                      verbose_prover=self.sim_options.verbose_prover,
                                      verbose_prefix="")

    self.sim.tape = new_tape

    self.stdout.write("\n")
    self.sim.verbose_print()

  ## Override methods in Cmd object ##
  def preloop(self):
    """Initialization before prompting user for commands.
       Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
    """
    cmd.Cmd.preloop(self)   ## sets up command completion
    self._hist    = []      ## No history yet
    self._locals  = {}      ## Initialize execution namespace for user
    self._globals = {}

  def postloop(self):
    """Take care of any unfinished business.
       Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
    """
    cmd.Cmd.postloop(self)   ## Clean up command completion
    print "Powering down...\n"

  def precmd(self, line):
    """ This method is called after the line has been input but before
        it has been interpreted. If you want to modifdy the input line
        before execution (for example, variable substitution) do it here.
    """
    self._hist += [ line.strip() ]
    return line

  def postcmd(self, stop, line):
    """If you want to stop the console, return something that evaluates to true.
       If you want to do some post command processing, do it here.
    """
    self.cmdnum += 1
    self.prompt = "%d> " % (self.cmdnum,)
    return stop

  def default(self, line):       
    """Called on an input line when the command prefix is not recognized.
       In that case we execute the line as Python code.
    """
    print "Unknown command:",line
    self.do_help(None)


if __name__ == "__main__":
  from optparse import OptionParser, OptionGroup
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  # TODO: Combine optparsers from MacroMachine, Enumerate and here.
  parser.add_option("-b", "--no-backsymbol", dest="backsymbol",
                    action="store_false", default=True,
                    help="Turn off backsymbol macro machine")
  parser.add_option("-p", "--no-prover", dest="prover",
                    action="store_false", default=True,
                    help="Turn off proof system")
  parser.add_option("-r", "--recursive", action="store_true", default=False, 
                    help="Turn on recursive proof system")
  parser.add_option("-n", "--block-size", type=int,
                    help="Block size to use in macro machine simulator "
                    "(default is to guess with the block_finder algorithm)")
  
  (options, args) = parser.parse_args()

  options.quiet   = False
  options.verbose = True
  options.manual  = True

  options.compute_steps = False

  options.print_loops = 1
  
  if options.verbose:
    options.verbose_simulator = True
    options.verbose_prover = True
    options.verbose_block_finder = True
  
  # Verbose block finder
  Block_Finder.DEBUG = options.verbose_block_finder
  
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
  
  BBconsole = BBConsole(ttable, options)
  BBconsole.cmdloop() 
