import getopt
import os
import string
import sys

from IO import IO

def open_infile(infilename):
  """Create input file based on a filename."""
  if not infilename or infilename == "-":
    return sys.stdin
  else:
    return file(infilename, "r")

def open_outfile(outfilename):
  """Create output file based on filename."""
  if outfilename == "-":
    return sys.stdout
  else:
    if os.path.exists(outfilename):
      sys.stderr.write("Output text file, '%s', exists\n" % outfilename)
      if string.lower(raw_input("Overwrite? ")) not in ("y", "yes"):
        return None
    return file(outfilename, "w")

def Generator_Option_Parser(argv, extra_opt, ignore_infile = True):
  """
  extra_opt = list of (opt, type_func, default_val, is_required, has_val)
  """
  opts = [("states"    , int, None , True , True),
          ("symbols"   , int, None , True , True),
          ("tape"      , int, 10000, False, True),
          ("steps"     , int, 10000, False, True),
          ("infile"    , str, None , False, True),
          ("outfile"   , str, None , False, True),
          ("log_number", int, None , False, True)] + extra_opt
  ignore_opts = []
  if ignore_infile:
    ignore_opts.append("infile")
  opts, args = Option_Parser(argv, opts, help_flag = True, no_mult = True,
                             ignore_opts = ignore_opts)

  # The furthest that the machine can travel in n steps is n+1 away from the
  # origin.  It could travel in either direction so the tape need not be longer
  # than 2 * max_steps + 3
  if opts["tape"] > 2 * opts["steps"] + 3:
    opts["tape"] = 2 * opts["steps"] + 3

  # Default output filename is based off of parameters.
  if not opts["outfile"]:
    opts["outfile"] = "%d.%d.%d.%d.out" % (opts["states"], opts["symbols"],
                                           opts["tape"], opts["steps"])
  opts["outfilename"] = opts["outfile"]
  opts["outfile"] = open_outfile(opts["outfilename"])
  if not opts["outfile"]:
    sys.exit(1)

  opts["infilename"] = opts["infile"]
  if not ignore_infile:
    opts["infile"] = open_infile(opts["infilename"])

  return opts, args

def Read_Atributes(input_file):
  temp_in = IO(input_file, None)
  line = temp_in.read_result()
  input_file.seek(0)
  return line[1:5]

def Filter_Option_Parser(argv, extra_opt, ignore_outfile = False):
  """
  extra_opt = list of (opt, type_func, default_val, is_required, has_val)
  """
  opts = [("tape"      , int, None, False, True),
          ("steps"     , int, None, False, True),
          ("infile"    , str, None, True , True),
          ("outfile"   , str, None, False, True),
          ("log_number", int, None, False, True)] + extra_opt
  ignore_opts = []
  if ignore_outfile:
    ignore_opts.append("outfile")
  opts, args = Option_Parser(argv, opts, help_flag = True, no_mult = True,
                             ignore_opts = ignore_opts)

  if not opts["infile"] or opts["infile"] == "-":
    sys.stderr.write("Filter_Option_Parser -- input from stdin currently not available\n")
    sys.exit(1)
  else:
    opts["infilename"] = opts["infile"]
    opts["infile"] = file(opts["infile"], "r")

  if not ignore_outfile:
    opts["states"], opts["symbols"], tape, steps = Read_Atributes(opts["infile"])
    # Tape length and max num steps default to those from the input file, but
    # can be changed by command line options.
    if not opts["tape"]:
      opts["tape"] = tape
    if not opts["steps"]:
      opts["steps"] = steps

    # The furthest that the machine can travel in n steps is n+1 away from the
    # origin.  It could travel in either direction so the tape need not be longer
    # than 2 * max_steps + 3
    if opts["tape"] > 2 * opts["steps"] + 3:
      opts["tape"] = 2 * opts["steps"] + 3

    if not opts["outfile"]:
      # Default output filename is based off of parameters.
      opts["outfile"] = "%d.%d.%d.%d.out" % (opts["states"], opts["symbols"],
                                             opts["tape"], opts["steps"])
    if opts["outfile"] == "-":
      opts["outfilename"] = "-"
      opts["outfile"] = sys.stdout
    else:
      if os.path.exists(opts["outfile"]):
        sys.stderr.write("Output text file, '%s', exists\n" % opts["outfile"])
        sys.exit(1)
      else:
        # This double use of opts["outfile"] is odd and possibly a bad idea,
        # but I don't think that the filename will ever be needed.
        opts["outfilename"] = opts["outfile"]
        opts["outfile"] = file(opts["outfile"], "w")

  return opts, args

def Option_Parser(argv, opts, help_flag = True, no_mult = True,
                  ignore_opts = []):
  """
  argv = list of command line options (sys.argv[1:])
  opts = list of expected options = (opt_name, type_func, default_val, is_required)
    opt_name = option name (e.g. "--states", "--symbols, etc.)
    type_func = function to convert string to correct type (e.g. int, float, str, etc.)
    default_val = value to default to if option not supplied.
    is_required = is this option required?
    has_val = does this option have a value
  help_flag = do you want --help to print usage message?
  no_mult = should multiple settings of an option cause an error?
  """
  # 'argv[0]' is the command called.
  usage = argv[0]
  # However we wish to strip off the directory structure and have only the
  # command name.
  usage = usage.split("/")[-1]
  opts_format2 = []
  if help_flag:
    usage +=  " [--help]"
    opts_format2.append("help")

  for opt, type_func, default_val, is_required, has_val in opts:
    if has_val:
      opts_format2.append("%s=" % opt)
      if opt not in ignore_opts:
        if is_required:
          usage += " --%s=" % opt
        elif default_val != None:
          usage += " [--%s=%s]" % (opt, repr(default_val))
        else:
          usage += " [--%s=]" % opt
    else:
      opts_format2.append(opt)
      if opt not in ignore_opts:
        if is_required:
          usage += " --%s" % opt
        else:
          usage += " [--%s]" % opt

  try:
    # Takes options with trailing equal sign.
    opt_val_pairs, args = getopt.getopt(argv[1:], "", opts_format2)
  except getopt.GetoptError:
    sys.stderr.write("%s\n" % usage)
    sys.exit(1)

  result = {}

  for opt, val in opt_val_pairs:
    opt = opt.lstrip("-")
    if opt == "help" and help_flag:
      sys.stdout.write("%s\n" % usage)
      sys.exit(0)
    elif result.has_key(opt) and no_mult:
      sys.stderr.write("Option (%s) specified multiple times.\n%s\n" % (opt, usage))
      sys.exit(1)
    else:
      result[opt] = val
  for opt, type_func, default_val, is_required, has_val in opts:
    if result.has_key(opt):
      if has_val:
        result[opt] = type_func(result[opt])
      else:
        result[opt] = result[opt] == ""
    elif is_required:
      sys.stderr.write("Option (%s) required.\n%s\n" % (opt, usage))
      sys.exit(1)
    else:
      result[opt] = default_val

  return result, args
