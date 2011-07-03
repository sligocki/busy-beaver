#! /usr/bin/env python
#
# Fit_Recur.py
#
"""
For each input line, attempt to fit a recurrence relation to a list of integers
for that input line.  Integers are space separated.
"""

import sys, string, copy, numpy

def fit(series):
  max_term_size = 100000000

  series = [term for term in series if term < max_term_size]
  # if len(series) > 20:
  #   series = series[len(series)-20:]

  print series

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

      print " ",n,residue,

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
          else:
            print

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
          else:
            print

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
    else:
      print " ",n,residue,"failure"


if __name__ == "__main__":
  for line in sys.stdin:
    sequence = map(int,line.split())
    fit(sequence)
    print

