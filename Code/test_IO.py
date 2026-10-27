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


if __name__ == "__main__":
  unittest.main()
