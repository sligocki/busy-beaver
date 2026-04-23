"""
Simulate a TM with DirectSim and print every configuration matching a
generalized tape pattern like "0^inf 1^a 10^b C> 1^c 0^inf".

Variable exponents (a, b, c, ...) are matched against the actual tape content
and their values are printed whenever the pattern matches.

Usage:
  python3 Tape_Pattern_Sim.py <tm> "<pattern>" [--max-steps N]

Examples:
  python3 Tape_Pattern_Sim.py 1RB---_0RC0RD_1LD1RB_0LE0LC_1RA0LF_1LD1LE \
      "0^inf 1^a 10^b C> 1^c 0^inf"
  python3 Tape_Pattern_Sim.py 1RB3LB1RZ2RA_2LC3RB1LC2RA_3RB1LB3LC2RC \
      "3 33^m 2^k A> 1^n"
"""

from __future__ import annotations

import argparse
import re
from typing import Optional

from Direct_Simulator import DirectSimulator
import IO
from Parse_Config import INF, ParsedConfig, parse_tape_config


def _build_side_regex(elements: list[tuple]) -> tuple[str, list[tuple[str, int]]]:
  """Build a regex and capture-group metadata for one side of the tape.

  Returns:
    regex_str: the full regex string (without ^ and $ anchors)
    captures:  list of (var_name, block_len) in capture-group order
  """
  pieces: list[str] = []
  captures: list[tuple[str, int]] = []

  for block, count in elements:
    block_re = re.escape("".join(str(d) for d in block))
    if count is INF or isinstance(count, float):
      pieces.append(f"(?:{block_re})*")
    elif isinstance(count, int):
      if count == 1:
        pieces.append(block_re)
      else:
        pieces.append(f"(?:{block_re}){{{count}}}")
    else:
      # Variable name
      pieces.append(f"((?:{block_re})*)")
      captures.append((count, len(block)))

  return "".join(pieces), captures


def _match_side(
    syms: list[int],
    elements: list[tuple],
) -> Optional[dict[str, int]]:
  """Try to match a list of symbols against pattern elements.

  Returns a dict of variable -> count on success, or None.
  """
  regex_body, captures = _build_side_regex(elements)
  s = "".join(str(v) for v in syms)
  m = re.fullmatch(regex_body, s)
  if m is None:
    return None
  result: dict[str, int] = {}
  for i, (var_name, block_len) in enumerate(captures, start=1):
    result[var_name] = len(m.group(i)) // block_len
  return result


def match_pattern(
    sim: DirectSimulator,
    parsed: ParsedConfig,
) -> Optional[dict[str, int]]:
  """Check if sim's current config matches the parsed pattern.

  Returns variable bindings on match, or None.
  """
  if int(sim.state) != parsed.state:
    return None

  left_syms = [sim.tape.tape[i].value for i in range(sim.tape.index)]
  right_syms = [sim.tape.tape[i].value
                for i in range(sim.tape.index, len(sim.tape.tape))]

  if parsed.dir_left:
    # <C style: head symbol is last of left side
    if right_syms:
      left_syms.append(right_syms.pop(0))

  left_bindings = _match_side(left_syms, parsed.left)
  if left_bindings is None:
    return None
  right_bindings = _match_side(right_syms, parsed.right)
  if right_bindings is None:
    return None

  return {**left_bindings, **right_bindings}


def _count_str(count: int | float | str, bindings: dict[str, int]) -> str:
  if count is INF or isinstance(count, float):
    return "inf"
  if isinstance(count, str):
    return str(bindings[count])
  return str(count)


def format_match(bindings: dict[str, int], parsed: ParsedConfig) -> str:
  """Format the match as 'a=3, b=5  →  0^inf 1^3 10^5 C> 1^2 0^inf'."""
  var_str = ", ".join(f"{v}={bindings[v]}" for v in parsed.variables)

  parts: list[str] = []
  for block, count in parsed.left:
    parts.append("".join(str(d) for d in block) + "^" + _count_str(count, bindings))
  state_token = (f"<{parsed.state_name}" if parsed.dir_left
                 else f"{parsed.state_name}>")
  parts.append(state_token)
  for block, count in parsed.right:
    parts.append("".join(str(d) for d in block) + "^" + _count_str(count, bindings))

  config_str = " ".join(parts)
  if var_str:
    return f"{var_str}  →  {config_str}"
  return config_str


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Print every DirectSim config matching a tape pattern.")
  parser.add_argument("tm",
    help="TM string (e.g. 1RB0LA_1LB0RA), filename, or filename:record_num.")
  parser.add_argument("pattern",
    help='Generalized tape config, e.g. "0^inf 1^a 10^b C> 1^c 0^inf".')
  parser.add_argument("--max-steps", type=int, default=1_000_000,
    help="Stop after this many steps (default: 1,000,000).")
  args = parser.parse_args()

  tm = IO.get_tm(args.tm)
  parsed = parse_tape_config(args.pattern)
  sim = DirectSimulator(tm)

  while True:
    bindings = match_pattern(sim, parsed)
    if bindings is not None:
      print(f"Step {sim.step_num}: {format_match(bindings, parsed)}")

    if sim.halted:
      print(f"Halted at step {sim.step_num}")
      break
    if sim.step_num >= args.max_steps:
      print(f"Reached max-steps limit ({args.max_steps})")
      break
    sim.step()


if __name__ == "__main__":
  main()
