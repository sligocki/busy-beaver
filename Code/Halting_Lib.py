# Library for setting various halting conditions (especially into the protobufs).

import math
import pickle
from typing import Optional

from Algebraic_Expression import Expression
from Exp_Int import ExpInt, ExpTerm, tower_value, fractional_height, try_eval
import io_pb2
import Math


def big_int_approx_str(value):
  if value is None:
    return "N/A"
  if value in (math.inf, -math.inf):
    return str(value)

  if value < 10**10:
    return f"{try_eval(value):_}"

  (height, top) = tower_value(value)
  while top > 10**10:
    height += 1
    top = math.log10(top)

  if height == 0:
    # value = top is small enough to be an integer
    if top <= 0:
      return str(top)
    else:
      return f"~10^{math.log10(top):_.5f}"
  elif height == 1:
    # value = 10^top
    return f"~10^{top:_.5f}"
  else:
    assert height > 1, height
    return f"~10↑↑{fractional_height(value):_.5f}"

def big_int_approx_and_full_str(value):
  if value is None:
    return "N/A"

  approx_str = big_int_approx_str(value)
  if isinstance(value, ExpInt):
    return f"{approx_str}  =  {value}"
  elif 0 < value < 10**50:
    return f"{approx_str}  =  {value:_}"
  else:
    return approx_str

def big_int_approx_or_full_str(value):
  if value is None:
    return "N/A"

  if isinstance(value, ExpInt):
    return str(value)
  elif isinstance(value, Expression):
    return str(value)
  elif value < 10**9:
    return f"{value:_}"
  elif value == math.inf:
    return str(value)
  else:
    return big_int_approx_str(value)


_BIG_INT_MAX = 2**63 - 1
def set_big_int(field : io_pb2.BigInt, value):
  field.Clear()
  if isinstance(value, int):
    if abs(value) <= _BIG_INT_MAX:
      # For "small" (non-negative) integers, store them directly.
      # Setting with negative value will cause a ValueError here.
      field.int = value
    else:
      # For "big" integers, store them as serialized text.
      # Store as hex to avoid https://docs.python.org/3/library/stdtypes.html#integer-string-conversion-length-limitation
      field.hex_str = hex(value)
  elif isinstance(value, ExpInt):
    field.exp_int_pickle = pickle.dumps(value)
  else:
    raise TypeError(f"Unexpected type {type(value)}")

def get_big_int(field : io_pb2.BigInt):
  type = field.WhichOneof("big_int")
  if type == "int":
    return field.int
  elif type == "uint_old":
    return field.uint_old
  elif type == "hex_str":
    return int(field.hex_str, base=16)
  elif type == "exp_int_pickle":
    return pickle.loads(field.exp_int_pickle)
  elif type == "exp_int":
    return parse_exp_int(field.exp_int)
  elif type is None:
    return None
  else:
    return None
    raise NotImplementedError(type)


# Protobuf serialization and parsing
def serialize_exp_int(exp_int : ExpInt, field : io_pb2.ExpInt):
  set_big_int(field.const, exp_int.const)
  field.denom = exp_int.denom
  for term in exp_int.terms:
    serialize_exp_term(term, field.terms.add())

def serialize_exp_term(term : ExpTerm, field : io_pb2.ExpTerm):
  field.base = term.base
  set_big_int(field.coef, term.coef)
  set_big_int(field.exponent, term.exponent)

def parse_exp_int(field : io_pb2.ExpInt) -> ExpInt:
  if field.HasField("const"):
    const = get_big_int(field.const)
  else:
    const = field.const_old

  terms = [parse_exp_term(term) for term in field.terms]
  return ExpInt(terms, const, field.denom)

def parse_exp_term(field : io_pb2.ExpTerm) -> ExpTerm:
  if field.HasField("coef"):
    coef = get_big_int(field.coef)
  else:
    coef = field.coef_old

  exp = get_big_int(field.exponent)
  return ExpTerm(field.base, coef, exp)


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
