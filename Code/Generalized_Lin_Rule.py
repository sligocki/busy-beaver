"""
Tool for analyzing a TM to find "Generalized Lin Rules" (GLRs) which are
rules of the form (or left-right mirrored):
  * X (Ty) Y Z -(k)-> W X (Ty) Y
Where:
 - T is a state;
 - y is a symbol;
 - W, X, Y, Z are sequences (possibly empty) of symbols;
 - k is a fixed integer (number of base TM steps).

GLRs are useful because they can potentially be applied repeatedly. Ex:
  * X (Ty) Y Z^n -(nk)-> W^n X (Ty) Y

This is a generalization of:
  * Lin Recurrence (when Z is all 0s) and
  * Chain Steps (when Y & X are empty and Z = y)
  * and Chain Steps on Block and Backsymbol Macro Machines

This search is meant to be an alternative to Block_Finder.py which does
direct simulation of TMs with various fixed block sizes looking for block sizes
which have the most efficient use of Chain Steps.

Note: For simplicity, I actually only search for GLRs where Y is empty.
It turns out that any GLR has a "version" where Y is empty, so this does not
miss any GLRs.
"""

import argparse
import string

import Direct_Simulator
import IO


class Rule:
  def __init__(self, ttable=None, start_state=None):
    if ttable:
      # Start with a tape that is entirely undefined (None).
      self.sim = Direct_Simulator.DirectSimulator(ttable, init_state=start_state, init_symbol=None)
      self.start_state = start_state
      self.start_tape = {}

  def copy(self):
    new_rule = Rule()
    new_rule.sim = self.sim.copy()
    new_rule.start_state = self.start_state
    new_rule.start_tape = dict(self.start_tape)  # Copy start_tape.
    return new_rule

  def __str__(self):
    if self.start_tape:
      start_config = (
        # Left tape
        "".join(str(self.start_tape[pos])
                for pos in range(min(self.start_tape.keys()), 0)) +
        # TM head
        f" ({string.ascii_uppercase[self.start_state]}{self.start_tape[0]}) " +
        # Right tape
        "".join(str(self.start_tape[pos])
                for pos in range(1, max(self.start_tape.keys()) + 1)))
    else:
      start_config = f"({string.ascii_uppercase[self.start_state]}_)"

    end_symb = self.sim.tape.read(self.sim.tape.position)
    if end_symb is None:
      end_symb = "_"
    end_config = (
      # Left tape
      "".join(str(self.sim.tape.read(pos))
              for pos in range(self.sim.tape.pos_min,
                               self.sim.tape.position)) +
      # TM head
      f" ({string.ascii_uppercase[self.sim.state]}{end_symb}) " +
      # Right tape
      "".join(str(self.sim.tape.read(pos))
              for pos in range(self.sim.tape.position + 1,
                               self.sim.tape.pos_max + 1)))

    return f"{start_config} -({self.sim.step_num})-> {end_config}"

  def run(self, max_steps):
    """Run simulator until it falls off defined part of tape."""
    while (self.sim.tape.read() is not None and
           not self.sim.halted and self.sim.step_num < max_steps):
      self.sim.step()

  def split(self, symb):
    new_rule = self.copy()
    new_rule.sim.tape.write(symb)
    new_rule.start_tape[new_rule.sim.tape.position] = symb
    return new_rule


def enum_rules(ttable, max_size, max_steps):
  """Use a depth-first tree search to find all GLRs up to a certain tape size."""
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  rules = []
  for state in range(num_states):
    # Start with a trivial rule
    todo = [Rule(ttable, start_state = state)]
    while todo:
      rule = todo.pop(0)
      # print()
      # print(f" ... Start {str(rule)}")
      rule.run(max_steps)
      # print(f" ... End   {str(rule)}")
      if rule.sim.halted:
        pass
      elif rule.sim.step_num >= max_steps:
        # Timed out simulating .. could be infinite repeat ...
        print("Timed out:", str(rule))
        pass
      else:
        assert rule.sim.tape.read() is None, str(rule)
        if rule.sim.step_num > 0:
          yield rule
        if len(rule.start_tape) < max_size:
          # Now the TM head is looking at a not-yet-defined symbol on the tape.
          # Duplicate this sim, one copy with each possible symbol and push those
          # all back onto the todo stack.
          for symb in range(num_symbols):
            todo.append(rule.split(symb))

def is_gen_lin_rule(rule):
  if rule.start_state != rule.sim.state:
    return False

  if rule.sim.tape.position == rule.sim.tape.pos_min:
    # Left moving rule Check if it has the form:
    #  * Z <T X -> <T (X) W
    X = [rule.start_tape[pos]
         for pos in range(1, max(rule.start_tape.keys()) + 1)]
    XW = [rule.sim.tape.read(pos)
          for pos in range(rule.sim.tape.position + 1,
                           rule.sim.tape.pos_max + 1)]
    if X == XW[:len(X)]:
      return True
    else:
      return False
  else:
    assert rule.sim.tape.position == rule.sim.tape.pos_max, str(rule)
    # Right moving rule. Check if it has the form:
    #  * (X) T> Z -> W (X) T>
    X = [rule.start_tape[pos]
         for pos in range(min(rule.start_tape.keys()), 0)]
    WX = [rule.sim.tape.read(pos)
          for pos in range(rule.sim.tape.pos_min,
                           rule.sim.tape.position)]
    # print(" ...", str(rule), X, WX)
    if not X or X == WX[-len(X):]:
      return True
    else:
      return False


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  parser.add_argument("tm_line", type=int, nargs="?", default=1)
  parser.add_argument("--max-size", type=int, default=4)
  parser.add_argument("--max-steps", type=int, default=1000)
  args = parser.parse_args()

  ttable = IO.Text.load_TTable_filename(args.tm_file, args.tm_line)
  for rule in enum_rules(ttable, args.max_size, args.max_steps):
    # print(" ... Considering rule:", str(rule))
    if is_gen_lin_rule(rule):
      print(f"GLR: {str(rule)}")

if __name__ == "__main__":
  main()
