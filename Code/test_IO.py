import io
from pathlib import Path
import tempfile
import unittest
import zipfile

import Halting_Lib
import IO
from IO.TM_Record import TM_Record, parse_tm
from IO.StdText import Writer
import TM_Enum
from Macro import Turing_Machine


class IOTest(unittest.TestCase):
  def test_writer_halting(self):
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

  def test_zip_stdtext_roundtrip(self):
    tm_obj = parse_tm("1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")
    tm = TM_Enum.TM_Enum(tm_obj, allow_no_halt=False)
    record = TM_Record(tm_enum=tm)

    with tempfile.TemporaryDirectory() as tmpdir:
      zippath = Path(tmpdir) / "test.txt.zip"
      with IO.StdText.Writer(zippath) as writer:
        writer.write_record(record)

      with IO.StdText.Reader(zippath) as reader:
        records = list(reader)

      self.assertEqual(len(records), 1)
      self.assertEqual(records[0].tm().ttable_str(), "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")

  def test_zip_proto_roundtrip(self):
    tm_obj = parse_tm("1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")
    tm = TM_Enum.TM_Enum(tm_obj, allow_no_halt=False)
    record = TM_Record(tm_enum=tm)
    Halting_Lib.set_halting(record.proto.status, halt_steps=100, halt_score=200)

    with tempfile.TemporaryDirectory() as tmpdir:
      zippath = Path(tmpdir) / "test.pb.zip"
      with IO.Proto.Writer(zippath) as writer:
        writer.write_record(record)

      with IO.Proto.Reader(zippath) as reader:
        records = list(reader)

      self.assertEqual(len(records), 1)
      self.assertEqual(records[0].tm().ttable_str(), "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")
      self.assertEqual(Halting_Lib.get_big_int(records[0].proto.status.halt_status.halt_steps), 100)

  def test_zip_with_macosx_metadata(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      zippath = Path(tmpdir) / "test.txt.zip"
      with zipfile.ZipFile(zippath, "w") as zf:
        zf.writestr("__MACOSX/._test.txt", b"macosx metadata")
        zf.writestr("test.txt", "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA\n")

      with IO.Reader(zippath) as reader:
        records = list(reader)

      self.assertEqual(len(records), 1)
      self.assertEqual(records[0].tm().ttable_str(), "1RB1LC_1RC1RB_1RD0LE_1LA1LD_1RZ0LA")

  def test_guess_module_zip(self):
    with tempfile.TemporaryDirectory() as tmpdir:
      pb_zip = Path(tmpdir) / "archive_pb.zip"
      with zipfile.ZipFile(pb_zip, "w") as zf:
        zf.writestr("inner.pb", b"dummy")
      self.assertEqual(IO.General.guess_module(pb_zip), IO.Proto)

      csv_zip = Path(tmpdir) / "archive_csv.zip"
      with zipfile.ZipFile(csv_zip, "w") as zf:
        zf.writestr("inner.csv", "machine,status\n")
      self.assertEqual(IO.General.guess_module(csv_zip), IO.CSV)

      txt_zip = Path(tmpdir) / "archive_txt.zip"
      with zipfile.ZipFile(txt_zip, "w") as zf:
        zf.writestr("inner.txt", "1RB---\n")
      self.assertEqual(IO.General.guess_module(txt_zip), IO.StdText)

  def test_extended_stdtext_symbols(self):
    # 2 states, 12 symbols (0..11)
    row_a = "".join(f"{(s + 1) % 12}RB" for s in range(12))
    row_b = "".join(f"{s}LA" for s in range(12))
    tm_str = f"{row_a}_{row_b}"

    tm = parse_tm(tm_str)
    self.assertEqual(tm.num_states, 2)
    self.assertEqual(tm.num_symbols, 12)
    self.assertEqual(tm.ttable_str(), tm_str)

    # Check General.get_tm
    tm_gen = IO.General.get_tm(tm_str)
    self.assertEqual(tm_gen.ttable_str(), tm_str)

  def test_extended_stdtext_states(self):
    # 28 states (A..AB), 2 symbols
    rows = []
    for i in range(27):
      next_st = Turing_Machine.state_to_str(i + 1)
      rows.append(f"1R{next_st}1R{next_st}")
    # State 27 (AB): halts on 0, undefined on 1
    rows.append("1RZZ---")
    tm_str = "_".join(rows)

    tm = parse_tm(tm_str)
    self.assertEqual(tm.num_states, 28)
    self.assertEqual(tm.num_symbols, 2)
    self.assertEqual(tm.ttable_str(), tm_str)

    # 26 states machine: state Z is running state 25, ZZ is halt
    rows_26 = []
    for i in range(25):
      next_st = Turing_Machine.state_to_str(i + 1)
      rows_26.append(f"1R{next_st}1R{next_st}")
    rows_26.append("1RZZ---")  # Z (state 25) halts on 0 with ZZ
    tm_26_str = "_".join(rows_26)

    tm_26 = parse_tm(tm_26_str)
    self.assertEqual(tm_26.num_states, 26)
    self.assertEqual(tm_26.get_trans_object(0, 25).condition, Turing_Machine.HALT)
    self.assertEqual(tm_26.ttable_str(), tm_26_str)

  def test_halt_state_normalization(self):
    # Any state >= num_states is parsed as halt (-1).
    # For a 2-state TM, state C (value 2) is >= 2, so it halts.
    # When serialized back, 2-state TM uses 'Z'.
    tm = parse_tm("1RC---_------")
    self.assertEqual(tm.get_trans_object(0, 0).condition, Turing_Machine.HALT)
    self.assertEqual(tm.ttable_str(), "1RZ---_------")

  def test_bbbb_parse_tm(self):
    import BBBB

    transitions = BBBB.parse_tm("10RAA---_1RZZ---")
    self.assertEqual(transitions["A"][0], (10, "R", "AA"))
    self.assertIsNone(transitions["A"][1])
    self.assertEqual(transitions["B"][0], (1, "R", "ZZ"))
    self.assertIsNone(transitions["B"][1])


if __name__ == "__main__":
  unittest.main()
