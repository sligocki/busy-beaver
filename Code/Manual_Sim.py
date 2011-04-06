#! /usr/bin/env python

import sys, string, os
import cmd
# import cmd2 as cmd

from Macro import Turing_Machine, Simulator, Block_Finder, Tape
from Numbers.Algebraic_Expression import Expression_from_string
import IO

class BBConsole(cmd.Cmd):

  def __init__(self, TTable, options):
    cmd.Cmd.__init__(self)
    self.init_code(TTable, options)

  ## Command definitions ##
  def help_apply(self):
    print "\nTry to apply the specified rule or all rules if not specified (not implemented).\n"

  def do_EOF(self, args):
    """\nExit on system end of file character.\n"""
    return self.EOF_code(args)

  def do_exit(self, args):
    """\nExits from the console.\n"""
    return self.exit_code(args)

  def do_help(self, args):
    """\nGet help on commands 'help' or '?' with no arguments prints a list of commands
for which help is available.\n
'help <command>' or '? <command>' gives help on <command>.\n"""
    ## The only reason to define this method is for the help text in the doc string
    cmd.Cmd.do_help(self, args)

  def do_hist(self, args):
    """\nPrint a list of commands that have been entered.\n"""
    self.hist_code(args)

  def help_list(self):
    print "\nPrint the specified rule or all rules if not specified (not implemented).\n"

  def help_load(self):
    print "\nLoad the rules from the specified file (not implemented).\n"

  def help_mark(self):
    print "\nMark the starting configuration for a rule (not implemented).\n"

  def do_prover(self, args):
    """\nTurn prover on or off.\n"""
    self.prover_code(args)

  def do_quit(self, args):
    """\nExits from the console.\n"""
    return self.do_exit(args)

  def help_rule(self):
    print "\nGenerate a rule with name, if specified (not implemented).\n"

  def help_save(self):
    print "\nSave the rules to the specified file (not implemented).\n"

  def do_step(self, args):
    """\nTake n steps of the current machine (default: n = 1).\n"""
    self.step_code(args)

  def do_tape(self, args):
    """\nEnter a new tape and state - same format as output.\n"""
    self.tape_code(args)

  def default(self, line):       
    """\nCalled on an input line when the command prefix is not recognized.
In that case we execute the line as Python code.\n
    """
    print "\nUnknown command:",line
    self.record_hist = False
    self.do_help(None)

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
    #rl_length = readline.get_current_history_length()
    #print "readline history length (post): %d" % (rl_length,)
    #for i in xrange(rl_length):
    #  print "   %d: '%s'" % (i,readline.get_history_item(i))
    self.set_cmdnum(self.cmdnum + 1)

    if self.record_hist:
      self._hist_cmd += [ line.strip() ]
    else:
      self._hist_cmd += [ "" ]
      if self.readline:
        last_entry = self.readline.get_current_history_length() - 1
        self.readline.remove_history_item(last_entry)
      self.record_hist = True
    return stop

  def preloop(self):
    """Initialization before prompting user for commands.
       Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
    """
    cmd.Cmd.preloop(self) ## Sets up command completion
    self._hist_cmd  = []  ## No command history yet
    self._hist_save = []  ## No saved history yet
    self._locals    = {}  ## Initialize execution namespace for user
    self._globals   = {}

    if self.readline:
      save_history_cmd = os.path.expanduser("~/.bb_ms_history_cmd")
      try:
        self.readline.read_history_file(save_history_cmd)
      except IOError:
        pass

      self.swap_history()
      self._hist_cmd = self._hist_save

      save_history_tape = os.path.expanduser("~/.bb_ms_history_tape")
      try:
        self.readline.read_history_file(save_history_tape)
      except IOError:
        pass

      self.swap_history()

      self.set_cmdnum(len(self._hist_cmd) + 1)

  def postloop(self):
    """Take care of any unfinished business.
       Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
    """
    cmd.Cmd.postloop(self)   ## Clean up command completion

    if self.readline:
      save_history_cmd = os.path.expanduser("~/.bb_ms_history_cmd")
      self.readline.write_history_file(save_history_cmd)

      self.swap_history()
      save_history_tape = os.path.expanduser("~/.bb_ms_history_tape")
      self.readline.write_history_file(save_history_tape)

    print "Powering down...\n"

  def init_code(self, TTable, options):
    self.readline = False
    try:
      import readline
      self.readline = readline
    except ImportError:
      try:
        import pyreadline as readline
        self.readline = readline
      # if we fail both readline and pyreadline
      except ImportError:
        print "Unable to import 'readline', line editing will be limited."
    else:
      import rlcompleter
      if sys.platform == 'darwin':
        readline.parse_and_bind ("bind ^I rl_complete")
      else:
        readline.parse_and_bind("tab: complete")

    self.set_cmdnum(1)

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
    self.sim_prover_save = None

    self.num_states  = self.sim.machine.num_states
    self.num_symbols = self.sim.machine.num_symbols

    print "Welcome to the machine!\n"

    self.sim.verbose_print()

  def EOF_code(self, args):
    print
    return self.do_exit(args)

  def exit_code(self, args):
    print
    return -1

  def hist_code(self, args):
    num = 1
    com_prev = ""
    for com in self._hist_cmd:
      if com != "" and com != com_prev:
        print "%4d  %s" % (num,com)
        com_prev = com
      num += 1

  def complete_prover(self, text, line, begidx, endidx):
    choices = ['off','on']
    if not text:
      completions = choices
    else:
      completions = [opt for opt in choices if opt.startswith(text)]

    return completions

  def prover_code(self, args):
    error = False
    if args == '':
      if self.sim.prover:
        state = "on"
      else:
        state = "off"
      print "\nProver is %s.\n" % (state,)
    elif args == 'on':
      if self.sim.prover == None:
        if self.sim_prover_save == None:
          import Macro.Proof_System
          self.sim.prover = Macro.Proof_System.Proof_System(self.sim.machine,
                                                            recursive=self.sim.recursive,
                                                            compute_steps=self.sim.compute_steps,
                                                            verbose=self.sim.verbose_prover,
                                                            verbose_prefix=self.sim.verbose_prefix)
          self.sim.prover.allow_collatz = False 
        else:
          self.sim.prover = self.sim_prover_save
    elif args == 'off':
      if self.sim.prover != None:
        self.sim_prover_save = self.sim.prover
      self.sim.prover = None
    else:
      error = True

    if error:
      print "\n'%s' must be 'on' or 'off'.\n" % (args,)
      self.record_hist = False

  def step_code(self, args):
    steps = 1

    if args != '':
      try:
        steps = int(args)
      except ValueError:
        print "\n'%s' is not an integer.\n" % (args,)
        self.record_hist = False

    if self.sim.op_state != Turing_Machine.RUNNING:
      print "\nTuring Machine is no longer running.\n"
    else:
      for step in xrange(steps):
        if self.sim.op_state == Turing_Machine.RUNNING:
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
            print
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

  def tape_code(self, args):
    self.stdout.write("\n")
    self.stdout.flush()

    self.swap_history()
    tape_state_string = raw_input("   Tape: ")
    self.swap_history()

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
          print "\nTape symbol lengths don't match.\n"
          return
        if token[0].translate(None,string.digits[:self.num_symbols]) != "":
          print "\nSome of '%s' isn't in '%s'.\n" % (token[0],string.digits[:self.num_symbols])
          return
        if symbol_length == 1:
          new_symbol = int(token[0])
        else:
          new_symbol = Turing_Machine.Block_Symbol([int(c) for c in token[0]])
        token[0] = new_symbol
      elif token[0][0] == "(":
        if len(token[0]) != symbol_length + 2:
          print "\nBack symbol length doesn't match tape symbol length.\n"
          return
        back_index = i
      elif token[0][0] == "<":
        state_index = i
        tape_dir = 0
      elif token[0][-1] == ">":
        state_index = i
        tape_dir = 1
      else:
        print "\nUnrecognized tape entry, '%s'.\n" % (token,)
        return

    if back_index > -1:
      if tape_dir == 0:
        if state_index > back_index:
          print "\nState and backsymbol are out of order.\n"
          return
        elif state_index + 1 != back_index:
          print "\nState and backsymbol aren't together.\n"
          return
      else:
        if state_index < back_index:
          print "\nState and backsymbol are out of order.\n"
          return
        elif state_index - 1 != back_index:
          print "\nState and backsymbol aren't together.\n"
          return
      new_back_symbol = tape_parse[back_index][0][1:-1]
      if new_back_symbol.translate(None,string.digits[:self.num_symbols]) != "":
        print "\nSome of back symbol, '%s', isn't in '%s'.\n" % (new_back_symbol,string.digits[:self.num_symbols])
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
            print "\nTape exponent, '%s', isn't a number.\n" % (token[1],)
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
            print "\nTape exponent, '%s', isn't a number.\n" % (token[1],)
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
      print "\nState, '%s', not one of '%s'.\n" % (new_state,states[:self.num_states])
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

    if self.sim.prover == None:
      self.sim_options.prover = False
    else:
      self.sim_options.prover = True

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

  def set_cmdnum(self, value):
    self.cmdnum = value
    self.prompt = "%d> " % (self.cmdnum,)

  def swap_history(self):
    if self.readline:
      rl_size_history = self.readline.get_current_history_length()

      temp = []
      for line_num in xrange(rl_size_history):
        temp.append(self.readline.get_history_item(line_num+1))

      self.readline.clear_history()

      for line in self._hist_save:
        self.readline.add_history(line)

      self._hist_save = temp


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



if __name__ == "__main__":
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
  options.prover  = False

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
