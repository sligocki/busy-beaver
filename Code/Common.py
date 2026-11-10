"""
Shared constants and constructs.
"""

import sys
import traceback

from google.protobuf.json_format import MessageToJson

# Increase some annoying limits
sys.set_int_max_str_digits(0)
sys.setrecursionlimit(10_000)


def format_single_tb(tb, max_repeat=2, max_cycle_len=16) -> list[str]:
  extracted = traceback.extract_tb(tb)
  lines = ["Traceback (most recent call last):\n"]
  i = 0
  n = len(extracted)
  while i < n:
    found_cycle = False
    for k in range(1, max_cycle_len + 1):
      if i + 2 * k <= n:
        pattern = [(f.filename, f.lineno, f.name) for f in extracted[i : i + k]]
        next_chunk = [(f.filename, f.lineno, f.name) for f in extracted[i + k : i + 2 * k]]
        if pattern == next_chunk:
          reps = 1
          while i + (reps + 1) * k <= n:
            chunk = [(f.filename, f.lineno, f.name) for f in extracted[i + reps * k : i + (reps + 1) * k]]
            if chunk == pattern:
              reps += 1
            else:
              break
          if reps >= max_repeat:
            for f in extracted[i : i + k]:
              lines.append(f'  File "{f.filename}", line {f.lineno}, in {f.name}\n')
              if f.line:
                lines.append(f"    {f.line}\n")
            lines.append(f"  [Previous {k} frame(s) repeated {reps - 1} more times]\n")
            i += reps * k
            found_cycle = True
            break
    if not found_cycle:
      f = extracted[i]
      lines.append(f'  File "{f.filename}", line {f.lineno}, in {f.name}\n')
      if f.line:
        lines.append(f"    {f.line}\n")
      i += 1
  return lines


def condense_traceback_str(exc_type, exc_val, tb, max_repeat=2, max_cycle_len=16) -> str:
  chain = []
  curr = exc_val
  while curr is not None:
    chain.append(curr)
    if curr.__cause__ is not None:
      curr = curr.__cause__
    elif curr.__context__ is not None and not curr.__suppress_context__:
      curr = curr.__context__
    else:
      curr = None

  lines = []
  for idx, exc in enumerate(reversed(chain)):
    if idx > 0:
      prev = chain[len(chain) - idx]
      if prev.__cause__ is exc:
        lines.append("\nThe above exception was the direct cause of the following exception:\n\n")
      else:
        lines.append("\nDuring handling of the above exception, another exception occurred:\n\n")
    if exc.__traceback__:
      lines.extend(format_single_tb(exc.__traceback__, max_repeat, max_cycle_len))
    lines.extend(traceback.format_exception_only(type(exc), exc))
  return "".join(lines)


def condensed_excepthook(exc_type, exc_val, tb):
  if issubclass(exc_type, RecursionError):
    sys.stderr.write("\n" + "=" * 80 + "\n")
    sys.stderr.write("ERROR: Recursion depth exceeded!\n")
    sys.stderr.write("The state of the Turing Machine prior to failure is printed above.\n")
    sys.stderr.write("=" * 80 + "\n")
  sys.stderr.write(condense_traceback_str(exc_type, exc_val, tb))


def install_condensed_traceback_hook():
  sys.excepthook = condensed_excepthook


install_condensed_traceback_hook()


def print_pb(pb):
  pb_str = MessageToJson(pb, always_print_fields_with_no_presence=True)
  print(pb_str)


class GenContainer:
  """Generic container class"""

  def __init__(self, **args):
    for atr in args:
      self.__dict__[atr] = args[atr]


class Exit_Condition:
  """Basically an enum of Turing machine exit conditions."""

  # TODO(shawn): It'd be nice to convert these to strings or something less
  # cryptic. However, these constants have weaseled their way throughout the
  # code. For example, they are in Turing_Machine_Sim.c, Macro_Machine.c and
  # Dual_Machine.c :/
  ERROR = -1
  HALT = 0
  UNDEF_CELL = 3
  INFINITE = 4

  # Generic unknown condition, we should move to this and add extra info as
  # reason text (IO.Record.category_reason).
  UNKNOWN = 6
  OVER_TAPE = 1
  MAX_STEPS = 2
  TIME_OUT = 5
  NOT_RUN = 7
  OVER_STEPS_IN_MACRO = 8
  # Set of all unknown conditions
  UNKNOWN_SET = (UNKNOWN, OVER_TAPE, MAX_STEPS, TIME_OUT, NOT_RUN)

  names = {
    ERROR: "Error",
    HALT: "Halt",
    UNDEF_CELL: "Undefined_Cell",
    INFINITE: "Infinite",
    # TODO(shawn): Print out "Unknown" for all of these.
    UNKNOWN: "Unknown",
    OVER_TAPE: "Over_Tape",
    MAX_STEPS: "Max_Steps",
    TIME_OUT: "Time_Out",
    NOT_RUN: "Not_Run",
    OVER_STEPS_IN_MACRO: "Macro_Over_Steps",
  }
  condition_from_name = {name: cond for (cond, name) in names.items()}

  @classmethod
  def name(cls, cond):
    """Convert Exit_Conditions to strings."""
    return cls.names[cond]

  @classmethod
  def read(cls, name):
    """Read Exit_Condition strings into constants."""
    return cls.condition_from_name[name]


HALT_TRANS = (1, 1, -1)
HALT_STATE = -1
