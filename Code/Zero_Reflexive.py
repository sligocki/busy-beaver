import argparse
import sys
import time

import IO
from Macro import Turing_Machine


def is_zero_reflexive(tm : Turing_Machine.Simple_Machine) -> bool:
  for state_in in range(tm.num_states):
    # Only consider the 0 symbol transition.
    trans = tm.get_trans_object(state_in = state_in, symbol_in = tm.init_symbol)
    # NOTE: We count TMs with undefined transitions as ZF (some of their children will be).
    if state_in == trans.state_out or trans.condition == Turing_Machine.UNDEFINED:
      return True
  return False


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("infile")
  parser.add_argument("zr_outfile")
  parser.add_argument("non_zr_outfile")
  args = parser.parse_args()

  with IO.Proto.Writer(args.zr_outfile) as zr_writer, \
       IO.Proto.Writer(args.non_zr_outfile) as non_zr_writer:
    num_total = 0
    num_zero_reflexive = 0
    start_time = time.time()
    with IO.Reader(args.infile) as reader:
      for tm_record in reader:
        num_total += 1
        if is_zero_reflexive(tm_record.tm()):
          if zr_writer:
            zr_writer.write_record(tm_record)
          num_zero_reflexive += 1
        else:
          if non_zr_writer:
            non_zr_writer.write_record(tm_record)
        if num_total % 100_000 == 0:
          print(f" ... {num_zero_reflexive:_} / {num_total:_} = {num_zero_reflexive / num_total:.2%} ({time.time() - start_time:_.0f}s)")

    print(f"# Zero Reflexive TMs: {num_zero_reflexive:_} / {num_total:_} = {num_zero_reflexive / num_total:.2%} ({time.time() - start_time:_.0f}s)")

if __name__ == "__main__":
  main()
