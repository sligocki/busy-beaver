import TM_Enum

import io_pb2

from Macro import Turing_Machine


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

def unpack_tm(pack : bytes):
  return Turing_Machine.Simple_Machine(unpack_ttable(pack))


class TM_Record:
  """Collection of TM (TM_Enum) and results (io_pb2.TMRecord)."""
  def __init__(self, *, proto=None, tm=None):
    if proto:
      self.proto = proto
    else:
      self.proto = io_pb2.TMRecord()

    if tm:
      self.update_tm(tm)
    else:
      tm = unpack_tm(self.proto.tm.ttable_packed)
      self.tm_enum = TM_Enum.TM_Enum(tm)

  def update_tm(self, tm_enum : TM_Enum.TM_Enum):
    self.tm_enum = tm_enum
    self.proto.tm.ttable_packed = pack_tm(self.tm_enum.tm)

  def ttable_str(self):
    return self.tm_enum.tm.ttable_str()


  def standardize_halt_trans(self):
    """This should only be called if the TM has halted by reaching an
    undefined transition. In that case, edit the transition to be a standard
    halt transition."""
    assert self.is_halting()
    self.tm_enum.set_halt_trans(
      state_in = self.proto.status.halt_status.from_state,
      symbol_in = self.proto.status.halt_status.from_symbol)
    self.proto.tm.ttable_packed = pack_tm(self.tm_enum.tm)


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
