import argparse
import sys

from Common import Exit_Condition
import IO
import Lin_Recur_Detect
import Option_Parser


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--infile", required=True, help="Input file name.")
  parser.add_argument("--outfile", required=True, help="Output file name.")
  parser.add_argument("--log-number", required=True, type=int,
                      help="Log number to use in output file.")
  parser.add_argument("--max-steps", type=int, default=10000)
  args = parser.parse_args()

  infile = Option_Parser.open_infile(args.infile)
  outfile = Option_Parser.open_outfile(args.outfile, force=False)
  io = IO.IO(infile, outfile, args.log_number)

  for io_record in io:
    result = Lin_Recur_Detect.lin_search(io_record.ttable, max_steps=args.max_steps)

    if result:
      init_step, period = result
      recur_start = Lin_Recur_Detect.period_search(io_record.ttable, init_step, period)

      # If a Lin recurrence is detected, update the results.
      io_record.log_number = args.log_number
      io_record.extended        = io_record.category
      io_record.extended_reason = io_record.category_reason

      io_record.category = Exit_Condition.INFINITE
      io_record.category_reason = ("Lin_Recur", recur_start, period)

    io.write_record(io_record)

if __name__ == "__main__":
  main()
