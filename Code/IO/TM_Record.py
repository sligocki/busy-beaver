import string

import TM_Enum

import io_pb2

from Macro import Turing_Machine


# Parse TMs in standard text format.
SYMBOLS_DISPLAY = string.digits
DIRS_DISPLAY = "LR"
STATES_DISPLAY = string.ascii_uppercase
def parse_tm(line : str) -> Turing_Machine.Simple_Machine:
  """Read transition table given a standard text representation."""
  assert " " not in line, f"Invalid TM format: {line}"
  quints = []
  rows = line.strip().split("_")
  num_states = len(rows)
  max_symbol = 0
  for state_in, row in enumerate(rows):
    for symbol_in, i in enumerate(range(0, len(row), 3)):
      max_symbol = max(max_symbol, symbol_in)
      trans_str = row[i:i+3]
      assert len(trans_str) == 3, f"'{trans_str}' - {line}"
      if trans_str != "---":
        symbol_out = SYMBOLS_DISPLAY.find(trans_str[0])
        dir_out = DIRS_DISPLAY.find(trans_str[1])
        state_out = STATES_DISPLAY.find(trans_str[2])
        if state_out >= num_states:
          state_out = -1
        assert symbol_out >= 0,   f"'{trans_str}' - {line}"
        assert dir_out in [0, 1], f"'{trans_str}' - {line}"
        assert state_out >= -1,   f"'{trans_str}' - {line}"
        quints.append((state_in, symbol_in, symbol_out, dir_out, state_out))
  return Turing_Machine.tm_from_quintuples(quints, states = list(range(num_states)),
                                           symbols = list(range(max_symbol + 1)))


def _pack_trans_ints(symbol : int, dir : int, state : int,
                    is_newrow : bool) -> int:
  if dir not in [0, 1]:
    dir = 0
  assert -1 <= symbol < 7, symbol
  assert -1 <= state < 7, state
  assert dir in [0, 1], dir
  byte_int =  (symbol + 1) | ((state + 1) << 3) | (dir << 6) | (is_newrow << 7)
  assert 0 <= byte_int < 256, byte_int
  return byte_int

def _unpack_trans_ints(byte_int : int):
  symbol = (byte_int & 0b111) - 1
  state = ((byte_int >> 3) & 0b111) - 1
  dir = (byte_int >> 6) & 0b1
  is_newrow = bool((byte_int >> 7) & 0b1)
  return symbol, dir, state, is_newrow


def _pack_trans(trans : Turing_Machine.Transition, is_newrow : bool) -> int:
  if trans.condition == Turing_Machine.UNDEFINED:
    return _pack_trans_ints(symbol = -1, dir = 0, state = -1,
                           is_newrow = is_newrow)
  else:
    return _pack_trans_ints(symbol = trans.symbol_out, dir = trans.dir_out,
                           state = trans.state_out, is_newrow = is_newrow)


def _pack_tm(tm : Turing_Machine.Simple_Machine) -> bytes:
  pack = bytearray(tm.num_states * tm.num_symbols)
  i = 0
  for row in tm.trans_table:
    is_newrow = True
    for trans in row:
      pack[i] = _pack_trans(trans, is_newrow)
      is_newrow = False
      i += 1
  return bytes(pack)

def _unpack_tm(pack : bytes) -> Turing_Machine.Simple_Machine:
  quints = []
  state_in = -1
  for byte in pack:
    (symbol, dir, state, is_newrow) = _unpack_trans_ints(byte)
    if is_newrow:
      state_in += 1
      symbol_in = 0
    if symbol >= 0:
      quints.append((state_in, symbol_in, symbol, dir, state))
    symbol_in += 1
  return Turing_Machine.tm_from_quintuples(quints, states = list(range(state_in + 1)),
                                           symbols = list(range(symbol_in)))

def tm_to_list(tm : Turing_Machine.Simple_Machine, tm_list : io_pb2.TMList) -> None:
  tm_list.num_states = tm.num_states
  tm_list.num_symbols = tm.num_symbols
  del tm_list.ttable_list[:]
  for state in range(tm.num_states):
    for symbol in range(tm.num_symbols):
      trans = tm.get_trans_object(symbol, state)
      if trans.condition == Turing_Machine.UNDEFINED:
        symbol_out = -1
      else:
        symbol_out = trans.symbol_out
      tm_list.ttable_list.append(symbol_out)
      tm_list.ttable_list.append(trans.dir_out)
      tm_list.ttable_list.append(trans.state_out)
  assert len(tm_list.ttable_list) == 3 * tm.num_states * tm.num_symbols

def tm_from_list(tm_list : io_pb2.TMList) -> Turing_Machine.Simple_Machine:
  quints = []
  i = 0
  for state_in in range(tm_list.num_states):
    for symbol_in in range(tm_list.num_symbols):
      symbol_out, dir_out, state_out = tm_list.ttable_list[i:i+3]
      if symbol_out != -1:
        quints.append((state_in, symbol_in, symbol_out, dir_out, state_out))
      i += 3
  # assert i == len(tm_list.ttable_list), (i, len(tm_list.ttable_list))
  return Turing_Machine.tm_from_quintuples(quints,
                                           states = list(range(tm_list.num_states)),
                                           symbols = list(range(tm_list.num_symbols)))

def read_tm(proto_tm : io_pb2.TuringMachine) -> Turing_Machine.Simple_Machine:
  type = proto_tm.WhichOneof("ttable")
  if type == "ttable_packed":
    return _unpack_tm(proto_tm.ttable_packed)
  elif type == "ttable_str":
    return IO.StdText.parse_tm(proto_tm.ttable_str)
  elif type == "ttable_list":
    return tm_from_list(proto_tm.ttable_list)
  else:
    raise NotImplementedError(f"Unexpected ttable type: {type}")

def write_tm(tm : Turing_Machine.Simple_Machine, proto_tm : io_pb2.TuringMachine):
  if tm.num_states < 7 and tm.num_symbols < 7:
    proto_tm.ttable_packed = _pack_tm(tm)
  else:
    tm_to_list(tm, proto_tm.ttable_list)


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
    write_tm(self.tme.tm, self.proto.tm)


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
