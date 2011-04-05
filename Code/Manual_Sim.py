#! /usr/bin/env python

import sys, string, os, cmd

from Macro import Turing_Machine, Simulator, Block_Finder, Tape
from Numbers.Algebraic_Expression import Expression_from_string
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


class BBConsole(cmd.Cmd):

  def __init__(self, TTable, options):
    cmd.Cmd.__init__(self)
    self.cmdnum = 1
    self.prompt = "%d> " % (self.cmdnum,)
    self.record_hist = True

    self.misc_header = "Unimplemented commands"

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

    self.num_states  = self.sim.machine.num_states
    self.num_symbols = self.sim.machine.num_symbols

    print "Welcome to the machine!\n"

    self.sim.verbose_print()

  ## Command definitions ##
  def help_apply(self):
    print "Try to apply the specified rule or all rules if not specified (not implemented)"

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

  def help_list(self):
    print "Print the specified rule or all rules if not specified (not implemented)"

  def help_mark(self):
    print "Mark the starting configuration for a rule (not implemented)"

  def do_quit(self, args):
    """Exits from the console"""
    return self.do_exit(args)

  def help_prover(self):
    print "Turn prover on or off (not implemented)"

  def help_rule(self):
    print "Generate a rule with name, if specified (not implemented)"

  def do_step(self,args):
    """Take n steps of the current machine (default: n = 1)"""
    steps = 1

    if args != '':
      try:
        steps = int(args)
      except ValueError:
        print "'%s' is not an integer" % (args,)
        self.record_hist = False
        return

    for step in xrange(steps):
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
    """Enter a new tape and state - same format as output"""
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
          print "Tape symbol lengths don't match\n"
          return
        if token[0].translate(None,string.digits[:self.num_symbols]) != "":
          print "Some of '%s' isn't in '%s'\n" % (token[0],string.digits[:self.num_symbols])
          return
        if symbol_length == 1:
          new_symbol = int(token[0])
        else:
          new_symbol = Turing_Machine.Block_Symbol([int(c) for c in token[0]])
        token[0] = new_symbol
      elif token[0][0] == "(":
        if len(token[0]) != symbol_length + 2:
          print "Back symbol length doesn't match tape symbol length\n"
          return
        back_index = i
      elif token[0][0] == "<":
        state_index = i
        tape_dir = 0
      elif token[0][-1] == ">":
        state_index = i
        tape_dir = 1
      else:
        print "Unrecognized tape entry: %s\n" % (token,)
        return

    if back_index > -1:
      if tape_dir == 0:
        if state_index > back_index:
          print "State and backsymbol are out of order\n"
          return
        elif state_index + 1 != back_index:
          print "State and backsymbol aren't together\n"
          return
      else:
        if state_index < back_index:
          print "State and backsymbol are out of order\n"
          return
        elif state_index - 1 != back_index:
          print "State and backsymbol aren't together\n"
          return
      new_back_symbol = tape_parse[back_index][0][1:-1]
      if new_back_symbol.translate(None,string.digits[:self.num_symbols]) != "":
        print "Some of back symbol, '%s', isn't in '%s'\n" % (new_back_symbol,string.digits[:self.num_symbols])
        return
      if symbol_length == 1:
        new_back_symbol = int(new_back_symbol)
      else:
        new_back_symbol = Turing_Machine.Block_Symbol([int(c) for c in new_back_symbol])
    else:
      new_back_symbol = ""
    
    new_tape = Tape.Chain_Tape()
    new_tape.dir = tape_dir

    new_tape.tape = [[], []]
    for i in xrange(token_length):
      if i < state_index and (back_index == -1 or i < back_index):
        if tape_parse[i][1] == "Inf":
          expo = Tape.INF
        elif tape_parse[i][1][0] == "(":
          expo = Expression_from_string(tape_parse[i][1])
        else:
          if not tape_parse[i][1].isdigit():
            print "Tape exponent '%s' isn't a number\n" % (token[1],)
            return
          expo = int(tape_parse[i][1])
        new_tape.tape[0].append(Tape.Repeated_Symbol(tape_parse[i][0],expo))
      if i > state_index and (back_index == -1 or i > back_index):
        if tape_parse[i][1] == "Inf":
          expo = Tape.INF
        elif tape_parse[i][1][0] == "(":
          expo = Expression_from_string(tape_parse[i][1])
        else:
          if not tape_parse[i][1].isdigit():
            print "Tape exponent '%s' isn't a number\n" % (token[1],)
            return
          expo = int(tape_parse[i][1])
        new_tape.tape[1].append(Tape.Repeated_Symbol(tape_parse[i][0],expo))

    new_tape.tape[1].reverse()
    new_tape.displace = 0

    self.sim_options.block_size = symbol_length

    if back_index >= 0:
      self.sim_options.backsymbol = True
    else:
      self.sim_options.backsymbol = False

    if tape_dir == 0:
      new_state = tape_parse[state_index][0][1]
    else:
      new_state = tape_parse[state_index][0][0]
        
    if new_state.translate(None,states[:self.num_states]) != "":
      print "State, '%s', not one of '%s'\n" % (new_state,states[:self.num_states])
      return

    new_state = Turing_Machine.Simple_Machine_State(states.index(new_state))

    if self.sim_options.backsymbol:
      new_state = Turing_Machine.Backsymbol_Macro_Machine_State(new_state,new_back_symbol)

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

    self.sim.state = new_state
    self.sim.dir   = tape_dir
    self.sim.tape  = new_tape

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
    return line

  def postcmd(self, stop, line):
    """If you want to stop the console, return something that evaluates to true.
       If you want to do some post command processing, do it here.
    """
    self.cmdnum += 1
    self.prompt = "%d> " % (self.cmdnum,)
    if self.record_hist:
      self._hist += [ line.strip() ]
    else:
      self._hist += [ "" ]
      self.record_hist = True
    return stop

  def default(self, line):       
    """Called on an input line when the command prefix is not recognized.
       In that case we execute the line as Python code.
    """
    print "Unknown command:",line
    self.record_hist = False
    self.do_help(None)


if __name__ == "__main__":
#  import rlcompleter
#  import readline
#
#  readline.parse_and_bind ("bind ^I rl_complete")

  try:
    import readline
  except ImportError:
    try:
      import pyreadline as readline
    # throw open a browser if we fail both readline and pyreadline
    except ImportError:
      import webbrowser
      webbrowser.open("http://ipython.scipy.org/moin/PyReadline/Intro#line-36")
      # throw open a browser
    #pass
  else:
    import rlcompleter
    if sys.platform == 'darwin':
      readline.parse_and_bind ("bind ^I rl_complete")
    else:
      readline.parse_and_bind("tab: complete")

  from optparse import OptionParser, OptionGroup
  # Parse command line options.
  usage = "usage: %prog [options] machine_file [line_number]"
  parser = OptionParser(usage=usage)
  # TODO: One variable for different levels of verbosity.
  Simulator.add_option_group(parser)
  (options, args) = parser.parse_args()

  options.quiet   = False
  options.verbose = True
  options.manual  = True

  options.compute_steps = True

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
