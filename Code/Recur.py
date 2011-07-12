#
# Recur.py
#
"""
Functions to help find recurrence relations - used to understand TMs and,
hopefully, prove things about them.  Currently this is a collect of functions
and not a class.  This may change as more is understood about this approach.
"""

import sys, string, copy, numpy

from Macro import Simulator, Block_Finder, Turing_Machine
import Output_Machine

def integer_solve(a,b):
  residue = 0

  num_var = len(a[0])
  num_eqn = len(b)

  num_steps = min(num_var,num_eqn)

  print "---",a
  print "---",b
  print ""

  for step in xrange(num_steps):
    if a[step][step] == 0:
      found = False
      for eqn in xrange(step+1,num_eqn):
        if a[eqn][step] != 0:
          temp    = a[step]
          a[step] = a[eqn]
          a[eqn]  = temp

          temp    = b[step]
          b[step] = b[eqn]
          b[eqn]  = temp

          found = True
          break

      if not found:
        residue = 1
        break

    c1 = a[step][step]
    for eqn in xrange(step+1,num_eqn):
      c2 = a[eqn][step]
      #print "-----",step,eqn,c1,c2

      a[eqn] = [c1*a_eqn - c2*a_step for [a_step,a_eqn] in zip(a[step],a[eqn])]
      b[eqn][0] = c1*b[eqn][0] - c2*b[step][0]

      print "-----",a
      print "-----",b
      print ""

  #print "---",num_var,num_eqn
  #print "---",num_steps
  print "---",a
  print "---",b
  print ""

  if residue == 0:
    all_zeros = num_var * [0]
    for eqn in xrange(num_steps,num_eqn):
      if a[eqn] != all_zeros or b[eqn] != [0,]:
        #print "...","bad"
        residue = 1
        break

  x = [[0] for i in xrange(0,num_var)]
  #print "---",x
  if residue == 0:
    for eqn in xrange(num_steps-1,-1,-1):
      #print "---",eqn
      [xcur,r] = divmod(b[eqn][0],a[eqn][eqn])
      #print "-----",xcur,r
      if r == 0:
        x[eqn][0] = xcur
        #print "-----",x
        for eqn2 in xrange(0,eqn):
          b[eqn2][0] -= a[eqn2][eqn]*x[eqn][0]
          a[eqn2][eqn] = 0
          #print "-----",a
          #print "-----",b
      else:
        residue = 1
        break

  #print "+++"

  return x,[residue,]

def recur_print(coefs,residue):
  recur_found = False
  recur_stop = False;

  if len(residue) > 0:
    residue = residue[0]

    print residue,

    if residue < 1e-12:
      int_coefs = [int(round(coef[0])) for coef in coefs]
      int_coefs.reverse()

      constant = int_coefs[-1]
      int_coefs = int_coefs[:-1]

      if not int_coefs or int_coefs[-1] != 0:
        recur_found = True

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
        else:
          print
      else:
        recur_stop = True

        print "failure",

        int_coefs = [coef[0] for coef in coefs]
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
    else:
      print "failure",

      int_coefs = [coef[0] for coef in coefs]
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
  else:
    print residue,"failure"

  return recur_found,recur_stop


def recur_fit(series,prefix=None):
  """Try to find a recurrence relation that fits the input series and print it"""
  # max_term_size = 100000000
  # series = [term for term in series if term < max_term_size]

  if len(series) > 20:
    series = series[len(series)-20:]

  if prefix:
    print prefix,

  print series

  recur_found = False

  for n in xrange(0,len(series)/2):
    a = [[1,] for i in xrange(len(series)-n)]
    for m in xrange(0,n):
      for i in xrange(len(series)-n):
        a[i].append(series[m+i])

    b = [[series[i],] for i in xrange(n,len(series))]

    # A = numpy.array(a)
    # B = numpy.array(b)
    #
    #  [x,residue,rank,sv] = numpy.linalg.lstsq(A,B)

    [x,residue] = integer_solve(a,b)

    if prefix:
      print prefix,

    print " ",n,
    (recur_found,recur_stop) = recur_print(x,residue)

    if recur_found or recur_stop:
      break

  return recur_found


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
