import io
import unittest

import Halting_Lib
from IO.TM_Record import TM_Record
from IO.StdText import Writer
import TM_Enum


class IOTest(unittest.TestCase):
  def test_writer_halting(self):
    from IO.TM_Record import parse_tm

    tm_obj = parse_tm("1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")
    tm = TM_Enum.TM_Enum(tm_obj, allow_no_halt=False)
    record = TM_Record(tm_enum=tm)

    # Set halting status
    Halting_Lib.set_halting(record.proto.status, halt_steps=12345, halt_score=67890)

    # Write to a string buffer using StdText.Writer
    out = io.StringIO()
    with Writer(out) as writer:
      writer.write_record(record)

    res = out.getvalue()
    self.assertIn("Halt 12345 67890", res)


if __name__ == "__main__":
  unittest.main()
