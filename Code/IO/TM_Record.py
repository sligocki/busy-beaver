import string

import TM_Enum

import io_pb2

from Macro import Turing_Machine


# Parse TMs in standard text format.
SYMBOLS_DISPLAY = string.digits
DIRS_DISPLAY = "LR"
STATES_DISPLAY = string.ascii_uppercase
def parse_ttable(line : str):
  """Read transition table given a standard text representation."""
  assert " " not in line, f"Invalid TM format: {line}"
  ttable = []
  rows = line.strip().split("_")
  num_states = len(rows)
  for row in rows:
    ttable_row = []
    for i in range(0, len(row), 3):
      trans_str = row[i:i+3]
      assert len(trans_str) == 3, trans_str
      if trans_str == "---":
        ttable_row.append((-1, 0, -1))
      else:
        symb_out = SYMBOLS_DISPLAY.find(trans_str[0])
        dir_out = DIRS_DISPLAY.find(trans_str[1])
        state_out = STATES_DISPLAY.find(trans_str[2])
        if state_out >= num_states:
          state_out = -1
        assert symb_out >= 0
        assert dir_out in [0, 1]
        assert state_out >= -1
        ttable_row.append((symb_out, dir_out, state_out))
    ttable.append(ttable_row)
  return ttable

def parse_tm(line : str) -> Turing_Machine.Simple_Machine:
  ttable = parse_ttable(line)
  return Turing_Machine.Simple_Machine(ttable)


def pack_trans_ints(symbol : int, dir : int, state : int,
                    is_newrow : bool) -> int:
  if dir not in [0, 1]:
    dir = 0
  assert -1 <= symbol < 7, symbol
  assert -1 <= state < 7, state
  assert dir in [0, 1], dir
  byte_int =  (symbol + 1) | ((state + 1) << 3) | (dir << 6) | (is_newrow << 7)
  assert 0 <= byte_int < 256, byte_int
  return byte_int

def unpack_trans_ints(byte_int : int):
  symbol = (byte_int & 0b111) - 1
  state = ((byte_int >> 3) & 0b111) - 1
  dir = (byte_int >> 6) & 0b1
  is_newrow = bool((byte_int >> 7) & 0b1)
  return symbol, dir, state, is_newrow


def pack_trans(trans : Turing_Machine.Transition, is_newrow : bool) -> int:
  if trans.condition == Turing_Machine.UNDEFINED:
    return pack_trans_ints(symbol = -1, dir = 0, state = -1,
                           is_newrow = is_newrow)
  else:
    return pack_trans_ints(symbol = trans.symbol_out, dir = trans.dir_out,
                           state = trans.state_out, is_newrow = is_newrow)


def pack_tm(tm : Turing_Machine.Simple_Machine) -> bytes:
  pack = bytearray(tm.num_states * tm.num_symbols)
  i = 0
  for row in tm.trans_table:
    is_newrow = True
    for trans in row:
      pack[i] = pack_trans(trans, is_newrow)
      is_newrow = False
      i += 1
  return bytes(pack)

def unpack_ttable(pack : bytes):
  ttable = []
  for byte in pack:
    (symbol, dir, state, is_newrow) = unpack_trans_ints(byte)
    if is_newrow:
      ttable.append([])
    ttable[-1].append((symbol, dir, state))
  return ttable


def read_tm(proto_tm : io_pb2.TuringMachine) -> Turing_Machine.Simple_Machine:
  type = proto_tm.WhichOneof("ttable")
  if type == "ttable_packed":
    return Turing_Machine.Simple_Machine(unpack_ttable(proto_tm.ttable_packed))
  elif type == "ttable_str":
    return IO.StdText.parse_tm(proto_tm.ttable_str)
  else:
    raise NotImplementedError(f"Unexpected ttable type: {type}")

def write_tm(tm : Turing_Machine.Simple_Machine, proto_tm : io_pb2.TuringMachine):
  if tm.num_states <= 7 and tm.num_symbols <= 8:
    proto_tm.ttable_packed = pack_tm(tm)
  elif tm.num_states <= 25 and tm.num_symbols <= 10:
    proto_tm.ttable_str = tm.ttable_str()
  else:
    raise NotImplementedError("Storing large TMs in protobuf has not been implemented yet. Max states = 25, max symbols = 10.")


class TM_Record:
  """Collection of TM (TM_Enum) and results (io_pb2.TMRecord)."""
  def __init__(self, *, proto=None, tm_enum=None):
    if proto:
      self.proto = proto
    else:
      self.proto = io_pb2.TMRecord()

    if tm_enum:
      self.update_tm(tm_enum)
    else:
      # Don't create TM unless needed (by calling tm_enum() or tm() below.)
      self.tme = None


  def update_tm(self, tm_enum : TM_Enum.TM_Enum) -> None:
    self.tme = tm_enum
    write_tm(self.tme.tm, self.proto.tm)

  def tm_enum(self):
    if not self.tme:
      tm = read_tm(self.proto.tm)
      self.tme = TM_Enum.TM_Enum(
        tm, allow_no_halt = self.proto.tm.allow_no_halt)
    return self.tme

  def tm(self):
    return self.tm_enum().tm

  def ttable_str(self) -> str:
    return self.tm().ttable_str()

  def clear_proto(self) -> None:
    for field in "status", "filter", "elapsed_time_us":
      self.proto.ClearField(field)


  def standardize_halt_trans(self):
    """This should only be called if the TM has halted by reaching an
    undefined transition. In that case, edit the transition to be a standard
    halt transition."""
    assert self.is_halting()
    self.tme.set_halt_trans(
      state_in = self.proto.status.halt_status.from_state,
      symbol_in = self.proto.status.halt_status.from_symbol)
    self.proto.tm.ttable_packed = pack_tm(self.tme.tm)


  def is_unknown_halting(self):
    return not self.proto.status.halt_status.is_decided

  def is_halting(self):
    assert self.proto.status.halt_status.is_decided
    return self.proto.status.halt_status.is_halting

  def is_unknown_quasihalting(self):
    return not self.proto.status.quasihalt_status.is_decided

  def is_quasihalting(self):
    assert self.proto.status.quasihalt_status.is_decided
    return self.proto.status.quasihalt_status.is_quasihalting

  # TODO: set_halting, ...
