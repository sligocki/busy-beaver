#
# Recur.py
#
"""
Functions to help find recurrence relations - used to understand TMs and,
hopefully, prove things about them.  Currently this is a collect of functions
and not a class.  This may change as more is understood about this approach.
"""

import sys, string, copy
# import numpy

from Macro import Simulator, Block_Finder, Turing_Machine
import Output_Machine

# Solve a system of linear equations with integer coefficients for an integer
# solution.  This uses Gaussian elimination and back-substitution.  Pivoting
# isn't important because the arithmetic is exact.
#
# This handles underdetermined, determined, and overdetermined systems.
# Currently, underdetermined systems are always flagged as unsuccessful.
#
# "a" is a list of lists representing a matrix.  Each sub-list is a row in the
# matrix.  "b" is a list representing a column vector.  The solution is a list
# representing a column vector such that "a x = b".
#
# The function return a boolean which is True if a solution is found and "x".
# If unsuccessful, x is the empty list.
def integer_solve(a,b,verbose=0):
  # Assume success
  success = True

  # Get the number of variable and equations
  num_var = len(a[0])
  num_eqn = len(b)

  # This is the number of steps in the Gaussian elimination
  num_steps = min(num_var,num_eqn)

  # Print diagnostics
  if verbose >= 1:
    print "---",a
    print "---",b
    print ""

  # See if the system is underdetermined
  if num_var > num_eqn:
    # Underdetermined systems are not solved (currently)
    success = False
  else:
    # Do Gaussian elimination on equation at a time
    for step in xrange(num_steps):
      # If the current diagonal entry is zero, find an equation that doesn't
      # have this problem and swap it for this current equation.
      if a[step][step] == 0:
        # Go through the remaining equations look for a suitable one.
        found = False
        for eqn in xrange(step+1,num_eqn):
          # If one is found swap the equations and the RHS
          if a[eqn][step] != 0:
            temp    = a[step]
            a[step] = a[eqn]
            a[eqn]  = temp

            temp    = b[step]
            b[step] = b[eqn]
            b[eqn]  = temp

            found = True
            break

        # If nothing is found, the solve is unsuccessful
        if not found:
          success = False
          break

      # Perform a step of Gaussian elimination
      c1 = a[step][step]
      for eqn in xrange(step+1,num_eqn):
        c2 = a[eqn][step]

        if verbose >= 2:
          print "-----",step,eqn,c1,c2

        a[eqn] = [c1*a_eqn - c2*a_step for [a_step,a_eqn] in zip(a[step],a[eqn])]
        b[eqn] = c1*b[eqn] - c2*b[step]

        if verbose >= 2:
          print "-----",a
          print "-----",b
          print ""

    if verbose >= 1:
      print "---",num_var,num_eqn
      print "---",num_steps
      print "---",a
      print "---",b
      print ""

    # If the Gaussian elimination was successful, check that any extra
    # equations now say "0 = 0" - meaning the original system was consistent.
    if success:
      all_zeros = num_var * [0]

      for eqn in xrange(num_steps,num_eqn):
        if a[eqn] != all_zeros or b[eqn] != 0:
          if verbose >= 1:
            print "...","bad"

          success = False
          break

    # If all is well, start doing backsubstitution.
    if success:
      # "x" is originally all zeros
      x = [0 for i in xrange(0,num_var)]
      if verbose >= 1:
        print "---",x

      # Go through the equations from bottom to top computing entries of x.
      for eqn in xrange(num_steps-1,-1,-1):
        if verbose >= 1:
          print "---",eqn

        # Do the appropriate, integer division
        [xcur,r] = divmod(b[eqn],a[eqn][eqn])

        if verbose >= 2:
          print "-----",xcur,r

        # If there is no remainder this step is successful
        if r == 0:
          # Record this part of the solution
          x[eqn] = xcur

          if verbose >= 2:
            print "-----",x

          # Remove this variable from all the other equations
          for eqn2 in xrange(0,eqn):
            b[eqn2] -= a[eqn2][eqn]*x[eqn]
            a[eqn2][eqn] = 0

            if verbose >= 2:
              print "-----",a
              print "-----",b
        else:
          # The computation is unsuccessfuly if the remainder isn't zero
          success = False
          break

    if verbose >= 1:
      print "+++"

  if not success:
    x = []

  return success,x


def recur_print(coefs):
  print " F(n) =",

  int_coefs = coefs
  int_coefs.reverse()

  constant  = int_coefs[-1]
  int_coefs = int_coefs[:-1]

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
  else:
    print


def recur_fit(series,prefix=None):
  """Try to find a recurrence relation that fits the input series and print it"""
  # Use the twenty largest entries
  if len(series) > 20:
    series = series[len(series)-20:]

  # Print a prefix if given
  if prefix:
    print prefix,

  # Print the series
  print series

  # Assume the worst
  recur_found = False

  # Try longer and longer recurrence relations starting with a constant
  for n in xrange(0,len(series)/2):
    # The coefficient of the constant is always one
    a = [[1,] for i in xrange(len(series)-n)]

    # Generate the rest of the matrix
    for m in xrange(0,n):
      for i in xrange(len(series)-n):
        a[i].append(series[m+i])

    # Generate the RHS
    b = series[n:]

    # See if "a x = b" has an integer solution
    [success,x] = integer_solve(a,b)

    # b = [[series[i],] for i in xrange(n,len(series))]
    #
    # A = numpy.array(a)
    # B = numpy.array(b)
    #
    # [xm,residue,rank,sv] = numpy.linalg.lstsq(A,B)
    #
    # success = True
    # if not residue or residue[0] <= 1e-12:
    #   success = False
    #
    # x = [xe[0] for xe in xm]
    
    if prefix:
      print prefix,

    print " ",n,

    # Print out result(s)
    if success:
      print "success",
      recur_print(x)
    else:
      print "failure"

    # On success, stop
    if success:
      break

  # Report success
  return success


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


def recur_TM(TTable, block_size, back, prover, recursive, options):
  # Construct Machine (Backsymbol-k-Block-Macro-Machine)
  m = Turing_Machine.make_machine(TTable)

  # If no explicit block-size given, use inteligent software to find one
  if not block_size:
    block_size = Block_Finder.block_finder(m, options)

  #if not options.quiet:
  #  Turing_Machine.print_machine(m)

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
  # max_term_size = 100000000

  while (sim.op_state == Turing_Machine.RUNNING and
         (options.loops == 0 or total_loops < options.loops)):
    # print "%10d" % sim.step_num,"  ",sim.tape.print_with_state(sim.state)

    sim.step()

    # if sim.step_num > max_term_size:
    #   break

    if len(sim.tape.tape[0]) == 1 or len(sim.tape.tape[1]) == 1:
      min_config = strip_config(sim.state,sim.dir,sim.tape.tape)

      if len(min_config[0]) + len(min_config[-1]) <= 100:
        if min_config in groups:
          # if len(groups[min_config]) >= 100:
          #   groups[min_config].pop(0)

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

  print Output_Machine.display_ttable(TTable),"|",
  print "%5d" % len(groups)

  for min_config in sorted_keys:
    group = groups[min_config]

    recur_all = False

    if len(group) >= 4:
      print "  ",len(group),min_config

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
        recur_found = recur_fit(series,"    ")
        recur_all = recur_all and recur_found
        print

      if recur_all:
        break

  print "  ",recur_all
  print
