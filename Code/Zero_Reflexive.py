import argparse
import sys

from Common import Exit_Condition
import IO
import Option_Parser


def is_zero_reflexive(ttable):
  for state_in in range(len(ttable)):
    # Only consider the 0 symbol transition.
    symbol_out, dir_out, state_out = ttable[state_in][0]
    if state_in == state_out:
      return True
  return False


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("tm_file")
  args = parser.parse_args()

  infile = Option_Parser.open_infile(args.tm_file)
  io = IO.IO(infile, None)

  num_total = 0
  num_zero_reflexive = 0
  for io_record in io:
    num_total += 1
    if is_zero_reflexive(io_record.ttable):
      num_zero_reflexive += 1

  print(f"# Zero Reflexive TMs: {num_zero_reflexive:_} / {num_total:_} = {num_zero_reflexive / num_total:.0%}")

if __name__ == "__main__":
  main()
