"""
Parse tape configuration strings like "0^inf 1^a 10^b C> 1^c 0^inf".

Exponents may be:
  - an integer literal  (e.g. ^3)
  - "inf"               (e.g. 0^inf) — math.inf
  - an identifier       (e.g. ^a)    — variable name (str)
  - absent              (e.g. "10")  — count = 1

Block characters are each a single digit, so "10" means the 2-symbol
block [1, 0], not the integer 10.

Implicit 0^inf edges: if the leftmost left-element is not already 0^inf,
one is prepended; likewise a 0^inf is appended to the right if absent.
"""

from __future__ import annotations

import math
import re
import string
from dataclasses import dataclass

# Maps single-character names to state indices.
# "!" is HALT (appended after all regular states).
STATES = string.ascii_uppercase + string.ascii_lowercase + "!"

INF = math.inf

# Token patterns
_STATE_RE = re.compile(r"^(<)([A-Za-z]+)$|^([A-Za-z]+)(>)$")
_BLOCK_RE  = re.compile(r"^(\d+)(?:\^(\w+))?$")


@dataclass
class ParsedConfig:
  state_name: str        # e.g. "C"
  state: int             # index into STATES
  dir_left: bool         # True if written as <C, False if C>
  # Each element is (block, count) where:
  #   block: list[int]  — symbol sequence for one repetition
  #   count: int | float | str  — int=fixed, inf=infinite, str=variable name
  left: list[tuple]
  right: list[tuple]
  variables: list[str]   # variable names in first-appearance order


def parse_tape_config(config_str: str) -> ParsedConfig:
  """Parse a tape configuration string into a ParsedConfig."""
  left_elements: list[tuple] = []
  right_elements: list[tuple] = []
  in_left = True
  dir_left: bool | None = None
  state_name: str | None = None
  variables: list[str] = []

  for token in config_str.split():
    if (m := _STATE_RE.fullmatch(token)):
      if m.group(1):  # <C form
        dir_left = True
        state_name = m.group(2)
      else:           # C> form
        dir_left = False
        state_name = m.group(3)
      in_left = False
      continue

    m = _BLOCK_RE.fullmatch(token)
    if not m:
      raise ValueError(f"Cannot parse tape token: {token!r}")

    block = [int(c) for c in m.group(1)]
    raw_count = m.group(2)
    if raw_count is None:
      count: int | float | str = 1
    elif raw_count == "inf":
      count = INF
    elif raw_count.isdigit():
      count = int(raw_count)
    else:
      count = raw_count  # variable name (str guaranteed by isdigit() check above)
      assert isinstance(count, str)
      if count not in variables:
        variables.append(count)

    if in_left:
      left_elements.append((block, count))
    else:
      right_elements.append((block, count))

  if state_name is None:
    raise ValueError(f"No state found in config: {config_str!r}")
  if dir_left is None:
    dir_left = False

  # Add implicit 0^inf edges.
  _zero_inf = ([0], INF)
  if not left_elements or left_elements[0] != _zero_inf:
    left_elements.insert(0, _zero_inf)
  if not right_elements or right_elements[-1] != _zero_inf:
    right_elements.append(_zero_inf)

  state = STATES.index(state_name)
  return ParsedConfig(
    state_name=state_name,
    state=state,
    dir_left=dir_left,
    left=left_elements,
    right=right_elements,
    variables=variables,
  )


def expand_config(parsed: ParsedConfig) -> tuple[int, list[int], list[int]]:
  """Expand a ParsedConfig with only fixed counts into (state, left_syms, right_syms).

  Raises ValueError if any variable or inf count is present (use for
  Visual_Simulator-style start configs).
  """
  def expand_side(elements: list[tuple], side_name: str) -> list[int]:
    syms: list[int] = []
    for block, count in elements:
      if count is INF or isinstance(count, float):
        continue  # skip implicit inf edges
      if isinstance(count, str):
        raise ValueError(
          f"Variable exponent {count!r} not allowed in start config "
          f"(got {side_name} element {block}^{count})"
        )
      syms.extend(block * count)
    return syms

  if parsed.dir_left:
    # <C: head symbol is last of left side; move it to front of right.
    left_syms = expand_side(parsed.left, "left")
    right_syms = expand_side(parsed.right, "right")
    if left_syms:
      right_syms.insert(0, left_syms.pop())
  else:
    left_syms = expand_side(parsed.left, "left")
    right_syms = expand_side(parsed.right, "right")

  return parsed.state, left_syms, right_syms
