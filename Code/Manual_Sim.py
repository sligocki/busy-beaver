#! /usr/bin/env python

import sys, string

from Macro import Turing_Machine, Simulator, Block_Finder
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

    def __init__(self, TTable, block_size, back, prover, recursive, options):
        cmd.Cmd.__init__(self)
        self.cmdnum = 1
        self.prompt = "%d> " % (self.cmdnum,)
        self.intro  = "Welcome to the machine!\n"  ## defaults to None

        # Construct Machine (Backsymbol-k-Block-Macro-Machine)
        m = Turing_Machine.make_machine(TTable)

        # If no explicit block-size given set it to 1
        if not block_size:
          block_size = 1

        if not options.quiet:
          print_machine(m)

        # Do not create a 1-Block Macro-Machine (just use base machine)
        if block_size != 1:
          m = Turing_Machine.Block_Macro_Machine(m, block_size)
        if back:
          m = Turing_Machine.Backsymbol_Macro_Machine(m)

        self.sim = Simulator.Simulator(m, recursive, enable_prover=prover, init_tape=True,
                                       compute_steps=options.compute_steps,
                                       verbose_simulator=options.verbose_simulator,
                                       verbose_prover=options.verbose_prover,
                                       verbose_prefix="")

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        num = 1
        for com in self._hist:
          print "%4d  %s" % (num,com)
          num += 1

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

    def do_exit(self, args):
        """Exits from the console"""
        print
        return -1

    def do_quit(self, args):
        """Exits from the console"""
        return self.do_exit(args)

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        print
        return self.do_exit(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

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
        print "Powering off..."

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

    def emptyline(self):    
        """Do nothing on empty input line"""
        self.onecmd(self.lastcmd)

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
  
  BBconsole = BBConsole(ttable, options.block_size, options.backsymbol,
                                options.prover, options.recursive, options)
  BBconsole.cmdloop() 
