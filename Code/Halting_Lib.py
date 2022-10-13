# Library for setting various halting conditions (especially into the protobufs).

from typing import Optional

import io_pb2


_BIG_INT_MAX = 2**64 - 1
def set_big_int(field : io_pb2.BigInt, value : int):
  if value <= _BIG_INT_MAX:
    # For "small" (non-negative) integers, store them directly.
    # Setting with negative value will cause a ValueError here.
    field.int = value
  else:
    # For "big" integers, store them as serialized text.
    # Store as hex to avoid https://docs.python.org/3/library/stdtypes.html#integer-string-conversion-length-limitation
    field.hex_str = hex(value)

def get_big_int(field : io_pb2.BigInt) -> Optional[int]:
  type = field.WhichOneof("big_int")
  if type == "int":
    return field.int
  elif type == "hex_str":
    return int(field.hex_str, base=16)
  else:
    return None


def set_halting(tm_status  : io_pb2.BBStatus,
                halt_steps : int,
                halt_score : int,
                from_state  : Optional[int],
                from_symbol : Optional[int]):
  """Specify that we know that this machine halts."""
  tm_status.halt_status.is_decided = True
  tm_status.halt_status.is_halting = True
  set_big_int(tm_status.halt_status.halt_steps, halt_steps)
  if halt_score is not None:
    set_big_int(tm_status.halt_status.halt_score, halt_score)
  if from_state is not None:
    tm_status.halt_status.from_state = from_state
  if from_symbol is not None:
    tm_status.halt_status.from_symbol = from_symbol

  # NOTE: We are treating Halting machines as Not Quasihalting.
  # Technically, Aaronson's definition calls Halting machines Quasihalting also.
  set_not_quasihalting(tm_status)

def set_not_halting(tm_status  : io_pb2.BBStatus,
                    inf_reason : io_pb2.InfReason):
  """Specify that we know that this machine does not halt."""
  tm_status.halt_status.is_decided = True
  tm_status.halt_status.is_halting = False
  tm_status.halt_status.inf_reason = inf_reason

def set_not_quasihalting(tm_status : io_pb2.BBStatus):
  """Specify that we know that this machine does not quasihalt."""
  tm_status.quasihalt_status.is_decided = True
  tm_status.quasihalt_status.is_quasihalting = False


def set_inf_recur(tm_status : io_pb2.BBStatus,
                  states_to_ignore,
                  states_last_seen):
  """Call for a TM that has some form of infinite recurrence.
  This detects if it has quasihalted (or if it will visit all states for all
  time) and sets the quasihalt_status (as well as halt_status since we know
  it's infinite).
  """
  if states_last_seen is None or states_to_ignore is None:
    # If we didn't keep track of the relevent info:
    tm_status.quasihalt_status.is_decided = False
    return

  q_state = None
  q_last_seen = -1
  for state, last_seen in states_last_seen.items():
    if state not in states_to_ignore:
      if last_seen > q_last_seen:
        q_state = state
        q_last_seen = states_last_seen[state]

  # Either way, we have made a conclusive decision.
  tm_status.quasihalt_status.is_decided = True
  if q_state == None:
    # We can definitively say that this machine does NOT quasihalt.
    # Instead it enters Lin Recurrence cycling through all states forever.
    tm_status.quasihalt_status.is_quasihalting = False
  else:
    tm_status.quasihalt_status.is_quasihalting = True
    # Quasihalting time is technically the step after the last time a specific
    # state was last seen.
    set_big_int(tm_status.quasihalt_status.quasihalt_steps, q_last_seen + 1)
    # Note: A TM may quasihalt at different times with respect to different
    # states. This is guaranteed to be the final quasihalt (max steps).
    tm_status.quasihalt_status.quasihalt_state = q_state
