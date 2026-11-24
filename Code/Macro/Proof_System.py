"""
Proof System which observes and attempts to prove patterns in computation.
"""

from NatExpr import approx_str
import copy
from enum import IntEnum
import math
import optparse
import sys
from collections import defaultdict
from optparse import OptionGroup, OptionParser, OptionValueError
import weakref

import Algebraic_Expression as ae
import Exp_Int
import Iterated_Expression
from Algebraic_Expression import (
  ConstantToExpression,
  Expression,
  NewVariableExpression,
  Term,
  Variable,
  VariableToExpression,
  VarPlusConstExpression,
  always_ge,
  substitute,
  variables,
)
from Macro import Rule_Func, Simulator, Tape, Turing_Machine
from Macro.Turing_Machine import LEFT, RIGHT
from NatExpr import ConstInt, NatExpr, is_const

# TODO: Remove this old naming.
Algebraic_Expression = Expression


class ProverLevel(IntEnum):
  """Hierarchy of proof system capabilities (each level enables all lower levels)."""

  NONE = 0  # No prover
  BASE = 1  # Level 1 Diff rules only (plain ints)
  EXP = 2  # + Recursive proofs & exponential acceleration (ExpInt)
  ITERATED = 3  # + Arbitrary iterated / meta-linear rules (Iterated_Expression)


DEFAULT_PROVER_LEVEL = ProverLevel.BASE
MAX_PROVER_LEVEL = ProverLevel.ITERATED

# Track prover-level CLI flag state per optparse.Values instance without
# polluting the parsed options object with private attributes.
_PROVER_LEVEL_PARSE_STATE: dict[int, dict[str, bool]] = {}


def parse_prover_level(value: str) -> ProverLevel:
  """Parse a CLI prover level string ('0'-'4' or 'max', case-insensitive)."""
  norm = value.strip().lower()
  if norm == "max":
    return MAX_PROVER_LEVEL
  try:
    level_int = int(norm)
  except ValueError as e:
    raise OptionValueError(
      f"Invalid prover level {value!r}: expected an integer 0-{int(MAX_PROVER_LEVEL)} or 'max'."
    ) from e
  if not (int(ProverLevel.NONE) <= level_int <= int(MAX_PROVER_LEVEL)):
    raise OptionValueError(f"Invalid prover level {value!r}: expected an integer 0-{int(MAX_PROVER_LEVEL)} or 'max'.")
  return ProverLevel(level_int)


def add_option_group(parser, default_prover_level: ProverLevel = DEFAULT_PROVER_LEVEL):
  """Add Proof_System options group to an OptParser parser object."""
  assert isinstance(parser, OptionParser)
  default_prover_level = ProverLevel(default_prover_level)

  def _get_state(values):
    key = id(values)
    state = _PROVER_LEVEL_PARSE_STATE.get(key)
    if state is None:
      state = {"used_level": False, "used_deprecated": False}
      _PROVER_LEVEL_PARSE_STATE[key] = state
      weakref.finalize(values, _PROVER_LEVEL_PARSE_STATE.pop, key, None)
    return state

  def _prover_level_callback(option, opt_str, value, parser):
    state = _get_state(parser.values)
    if state["used_deprecated"]:
      raise OptionValueError(f"Cannot combine {opt_str} with deprecated prover flags.")
    parser.values.prover_level = parse_prover_level(value)
    state["used_level"] = True

  def _deprecated_prover_flag_callback(option, opt_str, value, parser, level):
    state = _get_state(parser.values)
    if state["used_level"]:
      raise OptionValueError(f"Cannot combine --prover-level/-l with deprecated flag {opt_str}.")
    print(f"Warning: {opt_str} is deprecated; use --prover-level={int(level)}", file=sys.stderr)
    if not state["used_deprecated"]:
      parser.values.prover_level = level
    else:
      parser.values.prover_level = ProverLevel(max(parser.values.prover_level, level))
    state["used_deprecated"] = True

  group = OptionGroup(parser, "Proof System options")

  default_str = "max" if default_prover_level == MAX_PROVER_LEVEL else str(int(default_prover_level))
  group.add_option(
    "-l",
    "--level",
    "--prover-level",
    dest="prover_level",
    type="string",
    action="callback",
    callback=_prover_level_callback,
    default=default_prover_level,
    metavar="LEVEL",
    help=(
      f"Prover level (0=none, 1=base rules, 2=recursive + exponential rules, "
      f"3/max=arbitrary iterated rules). [Default: {default_str}]"
    ),
  )
  group.add_option("--verbose-prover", action="store_true")
  group.add_option(
    "--print-rules",
    "--rules",
    dest="print_rules",
    action="store_true",
    default=False,
    help="Print each newly proven rule (without step-by-step prover output).",
  )
  group.add_option(
    "-p",
    "--no-prover",
    action="callback",
    callback=_deprecated_prover_flag_callback,
    callback_args=(ProverLevel.NONE,),
    help="[Deprecated: use --prover-level=0] Turn OFF proof system.",
  )
  group.add_option(
    "-r",
    "--recursive",
    action="callback",
    callback=_deprecated_prover_flag_callback,
    callback_args=(ProverLevel.EXP,),
    help="[Deprecated: use --prover-level=2] Allow meta/recursive rules.",
  )
  group.add_option(
    "--no-limited-rules",
    dest="limited_rules",
    action="store_false",
    default=True,
    help="Force all rules to be full-tape rules.",
  )
  group.add_option(
    "--exp-linear-rules",
    action="callback",
    callback=_deprecated_prover_flag_callback,
    callback_args=(ProverLevel.EXP,),
    help="[Deprecated: use --prover-level=2] Allow accelerating Iterated_Rules.",
  )
  group.add_option(
    "--exp-meta-linear-rules",
    action="callback",
    callback=_deprecated_prover_flag_callback,
    callback_args=(ProverLevel.ITERATED,),
    help="[Deprecated: use --prover-level=3] Allow using Iterated_Rules in Meta Rules.",
  )
  group.add_option(
    "--no-const-blocks",
    dest="exp_const_blocks",
    action="store_false",
    default=True,
    help="Disable specializing depleted variable blocks to fixed constants during proofs.",
  )
  group.add_option(
    "--only-record-configs",
    action="store_true",
    default=False,
    help="Only save past configs to prover memory on record-breaking tape expansion steps [Experimental]",
  )
  group.add_option(
    "--exp-zero-exponents",
    action="store_true",
    default=False,
    help="Allow rules to start or end with 0-repetition blocks when safe [Experimental]",
  )
  group.add_option(
    "--exp-mod-iterated",
    action="store_true",
    default=False,
    help="Allow modular arithmetic on Iterated_Expression [Experimental]",
  )
  group.add_option(
    "--debug-reprove",
    action="store_true",
    default=False,
    help="Verify each newly proven rule by simulating it from its tightest minimum exponents [Debug]",
  )

  # A quick experiment shows that 100k past_configs -> 100MB, 1M -> 1GB RAM.
  group.add_option(
    "--max-prover-configs",
    type=int,
    default=100_000,
    help="Limit size of prover's previous configs (so avoid "
    "memory issues in situations where we're not applying any "
    "rules ...). "
    "[Default: %default]",
  )

  parser.add_option_group(group)


UNPROVEN_PARITY = "Unproven parity"
CONST_MISMATCH = "Const_Mismatch"


def _strip_outer_parens(s: str) -> str:
  while len(s) >= 2 and s[0] == "(" and s[-1] == ")":
    depth = 0
    matches_outer = True
    for i, ch in enumerate(s):
      if ch == "(":
        depth += 1
      elif ch == ")":
        depth -= 1
        if depth == 0 and i < len(s) - 1:
          matches_outer = False
          break
    if matches_outer and depth == 0:
      s = s[1:-1]
    else:
      break
  return s


def _format_config(left_blocks, state, dir, right_blocks):
  parts = []
  if left_blocks:
    parts.append(" ".join(left_blocks))
  parts.append(Tape.format_state_dir(state, dir))
  if right_blocks:
    parts.append(" ".join(right_blocks))
  return " ".join(parts)


def _format_steps(num_steps):
  if not num_steps:
    return "N/A"
  return _strip_outer_parens(str(num_steps))


class Rule:
  """Base type for Proof_System rules."""

  num: int | None = None
  is_limited: bool = False
  left_dist: int | None = None
  right_dist: int | None = None

  def make_limited(self, left_dist: int, right_dist: int):
    self.is_limited = True
    self.left_dist = left_dist
    self.right_dist = right_dist
    return self

  def _format_rule(self, rule_type: str, start_config: str, transitions: list[tuple[str, str]]) -> str:
    iter_lines = "\n".join(f"  {lhs} -> {rhs}" for lhs, rhs in transitions)
    return (
      f"{rule_type} {self.num}\n"
      f"Level: {self.level}\n"
      f"Start Config: {start_config}\n"
      f"Single Iter:\n{iter_lines}\n"
      f"Loops: {self.num_loops}\n"
      f"Steps: {_format_steps(self.num_steps)}"
    )


class Diff_Rule(Rule):
  """A rule where all exponents change like `x -> x + c` for some constant `c`."""

  def __init__(
    self,
    initial_tape,
    diff_tape,
    initial_state,
    num_steps,
    num_loops,
    rule_num,
    level: int,
    states_last_seen,
    left_dist: int | None = None,
    right_dist: int | None = None,
  ):
    # TODO: Use basic lists instead of tapes, we never use the symbols.
    # TODO: Have a variable list and a min list instead of packing both
    # into init_tape.
    # TODO: Or maybe we don't even need variables, we could just have the
    # things that depend on variables index directly into the tapes?
    # TODO: Actually, variables only appear in num_steps, so we don't even
    # need them if we are not computing steps.
    self.initial_tape = initial_tape
    self.diff_tape = diff_tape
    self.num_steps = num_steps
    self.initial_state = initial_state
    self.num_loops = num_loops
    self.num = rule_num  # Unique identifier.
    self.level = level
    self.states_last_seen = states_last_seen
    if left_dist is not None and right_dist is not None:
      self.make_limited(left_dist, right_dist)

    self.num_uses = 0  # Number of times this rule has been applied.

    # Figure out if any exponents decrease by > 1. If so, these can lead to
    # branching (Collatz) behavior, so it's good to know about!
    self.has_collatz_decrease = False
    for htape in self.diff_tape.tape:
      for block in htape:
        if block.num < -1:
          self.has_collatz_decrease = True

  def __repr__(self):
    transitions = []

    def format_start_and_collect(init_block, diff_block):
      sym = init_block.symbol
      num = init_block.num
      diff = diff_block.num
      if isinstance(num, Algebraic_Expression) and not num.is_const:
        var = num.variable_restricted()
        if is_const(diff):
          diff_val = diff.const if isinstance(diff, Algebraic_Expression) else int(diff)
          if diff_val > 0:
            transitions.append((str(var), f"{var} + {diff_val}"))
          elif diff_val < 0:
            transitions.append((str(var), f"{var} - {-diff_val}"))
        else:
          transitions.append((str(var), _strip_outer_parens(str(VariableToExpression(var) + diff))))
        return f"{sym}^({var} ≥ {num.const})"
      else:
        val = num.const if isinstance(num, Algebraic_Expression) else num
        return f"{sym}^{val}"

    left_start = [format_start_and_collect(ib, db) for ib, db in zip(self.initial_tape.tape[0], self.diff_tape.tape[0])]
    right_start = [
      format_start_and_collect(ib, db)
      for ib, db in zip(reversed(self.initial_tape.tape[1]), reversed(self.diff_tape.tape[1]))
    ]
    start_config = _format_config(left_start, self.initial_state, self.initial_tape.dir, right_start)
    return self._format_rule("Diff Rule", start_config, transitions)


MAX_PERM_COMPOSE_ORDER = 8


def _try_compose_permutation_rule(var_list, min_list, result_tape):
  """If `result_tape` permutes the variables in `var_list` (e.g. a swap rule),
  compose the transition with itself `order` times (the LCM of cycle lengths)
  until every variable returns to its original slot.

  Returns `(composed_min_list, composed_tape, order)` on success, or `None`.
  """
  result_list = [block.num for block in result_tape.tape[0] + result_tape.tape[1]]
  var_to_idx = {v: i for i, v in enumerate(var_list) if v is not None}
  if len(var_to_idx) < 2:
    return None

  src = {}
  for i, (var, min_val, res_expr) in enumerate(zip(var_list, min_list, result_list)):
    if var is None:
      if res_expr != min_val:
        return None
    else:
      res_vars = variables(res_expr)
      if len(res_vars) != 1:
        return None
      src_var = next(iter(res_vars))
      if src_var not in var_to_idx:
        return None
      src[i] = var_to_idx[src_var]

  # Must be a non-trivial bijection (permutation) on the variable indices.
  if len(set(src.values())) != len(src):
    return None
  if all(src[i] == i for i in src):
    return None

  # Compute permutation order (LCM of cycle lengths).
  visited = set()
  order = 1
  for start in src:
    if start in visited:
      continue
    cur_idx = start
    cycle_len = 0
    while cur_idx not in visited:
      visited.add(cur_idx)
      cur_idx = src[cur_idx]
      cycle_len += 1
    order = math.lcm(order, cycle_len)
    if order > MAX_PERM_COMPOSE_ORDER:
      return None
  if order < 2:
    return None

  req_min = list(min_list)
  cur = [VariableToExpression(v) if v is not None else m for v, m in zip(var_list, min_list)]
  cur_var_idx = {i: i for i in src}

  for step in range(order):
    # Ensure every variable slot satisfies min_list[i] before applying the next iteration.
    if step > 0:
      for i in src:
        orig_idx = cur_var_idx[i]
        orig_var = var_list[orig_idx]
        expr = cur[i]
        needed = min_list[i]
        lin = expr.as_strictly_linear() if hasattr(expr, "as_strictly_linear") else None
        if lin is not None:
          _, coef, const = lin
          if coef <= 0:
            return None
          if needed - const > 0:
            min_needed = Rule_Func.ceil_div(needed - const, coef)
            if min_needed > req_min[orig_idx]:
              req_min[orig_idx] = min_needed
        else:
          try:
            v0 = substitute(expr, {orig_var: req_min[orig_idx]})
            v1 = substitute(expr, {orig_var: req_min[orig_idx] + 1})
          except (Exp_Int.ExpIntGaveUp, Iterated_Expression.IteratedExprGaveUp, TypeError, ValueError):
            return None
          if v1 <= v0:
            return None
          bumps = 0
          while v0 < needed and bumps < 100:
            req_min[orig_idx] += 1
            bumps += 1
            try:
              v0 = substitute(expr, {orig_var: req_min[orig_idx]})
            except (Exp_Int.ExpIntGaveUp, Iterated_Expression.IteratedExprGaveUp, TypeError, ValueError):
              return None
          if v0 < needed:
            return None

    # Apply one iteration of the single-step rule.
    next_cur = list(cur)
    next_var_idx = {}
    for i in src:
      s = src[i]
      try:
        sub_val = substitute(result_list[i], {var_list[s]: cur[s]})
      except (Exp_Int.ExpIntGaveUp, Iterated_Expression.IteratedExprGaveUp, TypeError, ValueError, AssertionError):
        return None
      next_cur[i] = sub_val
      next_var_idx[i] = cur_var_idx[s]
    cur = next_cur
    cur_var_idx = next_var_idx

  assert all(cur_var_idx[i] == i for i in src), cur_var_idx

  composed_tape = result_tape.copy()
  idx = 0
  for d in range(2):
    for block in composed_tape.tape[d]:
      block.num = cur[idx]
      idx += 1

  return req_min, composed_tape, order


class Iterated_Rule(Rule):
  """A rule where all run counts change like `x -> m x + b` for constants `m, b`."""

  def __init__(
    self,
    var_list,
    min_list,
    func_list,
    result_tape,
    num_steps,
    num_loops,
    rule_num,
    states_last_seen,
    level: int,
    initial_state=None,
  ):
    assert len(var_list) == len(min_list) == len(func_list)
    self.var_list = var_list
    self.func_list = func_list
    self.block_list = [block.symbol for block in result_tape.tape[0] + result_tape.tape[1]]
    self.left_size = len(result_tape.tape[0])
    self.initial_state = initial_state
    self.dir = result_tape.dir
    self.num_steps = num_steps
    self.num_loops = num_loops
    self.num = rule_num
    self.states_last_seen = states_last_seen

    # Update minimums
    for i, func in enumerate(func_list):
      if func:
        min_list[i] = func.min
    self.min_list = min_list

    self.level = level
    self.num_uses = 0

    # Figure out which (if any) exponents are decreasing.
    self.is_decreasing = [False] * len(self.func_list)
    # Figure out if any exponents decrease by > 1. If so, these can lead to
    # branching (Collatz) behavior, so it's good to know about!
    self.has_collatz_decrease = False
    for i, func in enumerate(self.func_list):
      if func and func.is_decreasing:
        self.is_decreasing[i] = True
        if func.has_collatz_decrease:
          self.has_collatz_decrease = True

    # Rule is infinite if no exponent decreases.
    self.infinite = not any(self.is_decreasing)

  @staticmethod
  def try_gen(
    var_list,
    min_list,
    result_tape,
    num_steps,
    num_loops,
    rule_num,
    states_last_seen,
    level: int,
    initial_state=None,
  ):
    func_list = []
    for i, result_block in enumerate(result_tape.tape[0] + result_tape.tape[1]):
      if not var_list[i]:
        # Constant run_length (1, inf, or pinned constant c).
        if result_block.num != min_list[i]:
          return (
            None,
            f"Constant mismatch for block {i}: expected {min_list[i]}, got {result_block.num}",
          )
        func_list.append(None)

      else:
        # Variable run_length
        if variables(result_block.num) != {var_list[i]}:
          # Don't allow rules like: x -> 7 or x -> 3y+2
          return (
            None,
            (
              f"Variable mismatch for block {i}: expected {{{var_list[i]}}}, "
              f"got {variables(result_block.num)} from {result_block.num}"
            ),
          )
        res = None
        if hasattr(result_block.num, "as_strictly_linear"):
          res = result_block.num.as_strictly_linear()

        if res:
          (var, coef, const) = res
          assert var == var_list[i]
          if coef == 1:
            if const < 0:
              func_list.append(Rule_Func.Subtract_Func(var, min_list[i], -const))
            else:
              func_list.append(Rule_Func.Add_Func(var, min_list[i], const))
          else:
            func_list.append(Rule_Func.Mult_Func(var, min_list[i], coef, const))
        else:
          # always_ge is too crude for ExpInt - x, so we just evaluate at min_val
          val_at_min = substitute(result_block.num, {var_list[i]: min_list[i]})
          if val_at_min < min_list[i]:
            return (
              None,
              f"Iterated block {i} is not >= var at min_val: {result_block.num} ({val_at_min} < {min_list[i]})",
            )

          # Also check val at min_val + 1 to ensure it's increasing
          val_at_min_1 = substitute(result_block.num, {var_list[i]: min_list[i] + 1})
          if val_at_min_1 <= val_at_min:
            return (
              None,
              f"Iterated block {i} is not strictly increasing: {result_block.num}",
            )

          func_list.append(Rule_Func.Iterated_Func(var_list[i], min_list[i], result_block.num))
    return Iterated_Rule(
      var_list,
      min_list,
      func_list,
      result_tape,
      num_steps,
      num_loops,
      rule_num,
      states_last_seen,
      level,
      initial_state=initial_state,
    ), None

  def __repr__(self):
    def start_block(i):
      if self.var_list[i]:
        return f"{self.block_list[i]}^({self.var_list[i]} ≥ {self.min_list[i]})"
      else:
        return f"{self.block_list[i]}^{self.min_list[i]}"

    left_indices = list(range(self.left_size))
    right_indices = list(reversed(range(self.left_size, len(self.block_list))))
    left_start = [start_block(i) for i in left_indices]
    right_start = [start_block(i) for i in right_indices]

    transitions = []
    for i in left_indices + right_indices:
      if self.var_list[i]:
        func = self.func_list[i]
        if isinstance(func, Rule_Func.Add_Func) and func.const == 0:
          continue
        transitions.append((str(self.var_list[i]), _strip_outer_parens(str(func))))

    start_config = _format_config(left_start, self.initial_state, self.dir, right_start)
    return self._format_rule("Iterated Rule", start_config, transitions)


def _rule_signature(rule):
  """Canonical, variable-name-independent signature for deduplicating rules."""
  left_syms, right_syms = _rule_expected_symbols(rule)
  rule_dir = rule.initial_tape.dir if isinstance(rule, Diff_Rule) else rule.dir
  base = (
    type(rule).__name__,
    rule.initial_state,
    rule_dir,
    rule.is_limited,
    rule.left_dist,
    rule.right_dist,
    left_syms,
    right_syms,
  )
  if isinstance(rule, Diff_Rule):
    init_spec = []
    diff_spec = []
    for d in range(2):
      for init_b, diff_b in zip(rule.initial_tape.tape[d], rule.diff_tape.tape[d]):
        if isinstance(init_b.num, Algebraic_Expression):
          init_spec.append(("var", init_b.num.const))
        else:
          init_spec.append(("const", init_b.num))
        diff_spec.append(diff_b.num)
    return base + (tuple(init_spec), tuple(diff_spec))
  elif isinstance(rule, Iterated_Rule):
    slot_spec = []
    for i, (var, min_val, func) in enumerate(zip(rule.var_list, rule.min_list, rule.func_list)):
      if var is None:
        slot_spec.append(("const", min_val))
      else:
        f_str = str(func).replace(str(var), f"v{i}")
        slot_spec.append(("var", min_val, type(func).__name__, f_str))
    return base + (tuple(slot_spec),)
  return base + (repr(rule),)


def _rule_expected_symbols(rule):
  """Return `(left_symbols, right_symbols)` expected by `rule`."""
  if isinstance(rule, Diff_Rule):
    return (
      tuple(b.symbol for b in rule.initial_tape.tape[0]),
      tuple(b.symbol for b in rule.initial_tape.tape[1]),
    )
  return (
    tuple(rule.block_list[: rule.left_size]),
    tuple(rule.block_list[rule.left_size :]),
  )


def _rule_zero_min_slots(rule):
  """Return tuple of `(dir, idx, symbol)` for blocks in `rule` that allow 0 repetitions."""
  slots = []
  if isinstance(rule, Diff_Rule):
    for dir in range(2):
      for idx, block in enumerate(rule.initial_tape.tape[dir]):
        if isinstance(block.num, Algebraic_Expression) and block.num.const == 0:
          slots.append((dir, idx, block.symbol))
  elif hasattr(rule, "var_list") and hasattr(rule, "min_list") and hasattr(rule, "block_list"):
    for flat_idx, (var, min_val, sym) in enumerate(zip(rule.var_list, rule.min_list, rule.block_list)):
      if var is not None and min_val == 0:
        if flat_idx < rule.left_size:
          slots.append((0, flat_idx, sym))
        else:
          slots.append((1, flat_idx - rule.left_size, sym))
  return tuple(slots)


def _insert_tuple_at(tup, idx, val):
  return tup[:idx] + (val,) + tup[idx:]


def _remove_tuple_at(tup, idx):
  return tup[:idx] + tup[idx + 1 :]


def _prepare_tape_for_rule(rule, start_tape):
  """Prepare `start_tape` for `rule`, slicing if limited and inserting any omitted 0-min blocks."""
  exp_syms = _rule_expected_symbols(rule)
  zero_slots = _rule_zero_min_slots(rule)
  slots_by_dir = {0: [], 1: []}
  for slot_dir, slot_idx, sym in zero_slots:
    slots_by_dir[slot_dir].append((slot_idx, sym))

  prepared = start_tape.copy()
  save = [[], []]
  eff_dist = [rule.left_dist, rule.right_dist]

  for dir, dist in ((0, rule.left_dist), (1, rule.right_dist)):
    half = prepared.tape[dir]
    exp = exp_syms[dir]
    if rule.is_limited:
      if len(half) >= dist and tuple(b.symbol for b in _slice_tape_tail(half, dist)) == exp:
        save[dir] = _slice_tape_head(half, dist)
        prepared.tape[dir] = _slice_tape_tail(half, dist)
        eff_dist[dir] = dist
        continue
      matched_slot = False
      if dist > 0 and len(half) >= dist - 1:
        tail = _slice_tape_tail(half, dist - 1)
        tail_syms = tuple(b.symbol for b in tail)
        for slot_idx, sym in slots_by_dir[dir]:
          if _insert_tuple_at(tail_syms, slot_idx, sym) == exp:
            save[dir] = _slice_tape_head(half, dist - 1)
            prepared.tape[dir] = tail[:slot_idx] + [Simulator.Tape.Repeated_Symbol(sym, 0)] + tail[slot_idx:]
            eff_dist[dir] = dist - 1
            matched_slot = True
            break
      if not matched_slot:
        save[dir] = _slice_tape_head(half, dist)
        prepared.tape[dir] = _slice_tape_tail(half, dist)
        eff_dist[dir] = dist
    else:
      cur_syms = tuple(b.symbol for b in half)
      if cur_syms != exp and len(half) == len(exp) - 1:
        for slot_idx, sym in slots_by_dir[dir]:
          if _insert_tuple_at(cur_syms, slot_idx, sym) == exp:
            prepared.tape[dir] = half[:slot_idx] + [Simulator.Tape.Repeated_Symbol(sym, 0)] + half[slot_idx:]
            break

  return prepared, save[0], save[1], eff_dist[0], eff_dist[1]


def _normalize_half_tape(half_tape):
  """Remove zero-count blocks and merge adjacent blocks with the same symbol."""
  result = []
  for block in half_tape:
    if block.num == 0:
      continue
    if result and result[-1].symbol == block.symbol:
      result[-1].num += block.num
    else:
      result.append(block)
  return result


def _splice_limited_half_tape(save_prefix, rule_tail, dist):
  """Splice `save_prefix` and `rule_tail`, normalizing zero blocks and merging at the boundary."""
  norm_tail = _normalize_half_tape(rule_tail)
  if not save_prefix:
    return norm_tail, dist
  if norm_tail and save_prefix[-1].symbol == norm_tail[0].symbol:
    merged = save_prefix[-1].copy()
    merged.num += norm_tail[0].num
    return save_prefix[:-1] + [merged] + norm_tail[1:], dist + 1
  return save_prefix + norm_tail, dist


# TODO: Try out some other stripped_configs
def _slice_tape_tail(seq, dist):
  """Return the last `dist` elements of `seq` (handling dist == 0 safely)."""
  if dist == 0:
    return seq[:0]
  return seq[-dist:]


def _slice_tape_head(seq, dist):
  """Return all but the last `dist` elements of `seq` (handling dist == 0 safely)."""
  if dist == 0:
    return seq[:]
  return seq[:-dist]


def stripped_info(block):
  """Get an abstraction of a tape block. We try to prove rules between
  configuration which have the same abstraction.
  """
  if getattr(block.num, "is_inf", False):
    return block.symbol, -1
  # Note: We treat singleton blocks specially. It's quite common to have many singleton blocks
  # in a rule that do not change. With const-block feature, we could re-discover this automatically.
  # But it turns out that this has an unexpected positive side-effect as well. It means we never
  # try to start proving a rule (for decreasing exponents) when that exponent is 1 which would fail.
  elif block.num == 1:
    return block.symbol, 1
  else:
    return block.symbol


def strip_config(state, dir, tape):
  """Return a generalized configuration removing the non-1 repetition counts from the tape."""
  return (
    state,
    dir,
    tuple(map(stripped_info, tape[0])),
    tuple(map(stripped_info, tape[1])),
  )


class Past_Config:
  """A record of info from past instances of a stripped_config."""

  def __init__(self):
    self.times_seen = 0
    self.last_loop_num = None
    self.last_delta = None
    # self.delta_loops = set()

  def __repr__(self):
    return repr(self.__dict__)

  def log_config(self, loop_num):
    """Decide whether we should try to prove a rule.

    Currently, we try to prove a rule we've seen happen twice (not necessarily
    consecutive) with the same num of loops (last_delta or delta_loops).
    """
    # First time we see stripped_config, store loop_num.
    if self.last_loop_num is None:
      self.last_loop_num = loop_num
      self.times_seen += 1
      return False

    # Next store last_delta. If we have a last_delta but it hasn't repeated,
    # then update the new delta. (Note: We can only prove rules that take
    # the same number of loops each time.)
    delta = loop_num - self.last_loop_num
    if not self.last_delta or self.last_delta != delta:
      self.last_delta = delta
      # self.delta_loops = set()
      # self.delta_loops.add(delta)
      self.last_loop_num = loop_num
      self.times_seen += 1
      return False

    # Now we can finally try a proof.
    return True


# Possible values for ProverResult.condition
NOTHING_TO_DO = "Nothing_To_Do"  # No rule applies, nothing to do.
APPLY_RULE = "Apply_Rule"  # Rule applies, but only finitely many times.
INF_REPEAT = "Inf_Repeat"  # Rule applies infinitely.
OVER_LOOPS = "Over_Loops"  # Proving rule would exceed remaining loop budget.


class ProverResult:
  def __init__(
    self,
    condition,
    *,
    new_tape=None,
    num_base_steps=None,
    states_last_seen=None,
    left_dist=None,
    right_dist=None,
    delta_loop=None,
    remaining_loops=None,
  ):
    self.condition = condition
    self.new_tape = new_tape
    self.num_base_steps = num_base_steps
    self.states_last_seen = states_last_seen
    self.left_dist = left_dist
    self.right_dist = right_dist
    self.delta_loop = delta_loop
    self.remaining_loops = remaining_loops


class Proof_System:
  """Stores past information, looks for patterns and tries to prove general
  rules when it finds patterns.
  """

  def __init__(self, machine, options, verbose_prefix):
    assert isinstance(options, optparse.Values)

    self.machine = machine
    self.options = options
    # If self.frozen == True, no new rules will be proven.
    self.frozen = False
    self.prover_level = ProverLevel(options.prover_level)
    self.exp_zero_exponents = getattr(options, "exp_zero_exponents", False)
    self.exp_mod_iterated = getattr(options, "exp_mod_iterated", False)
    Iterated_Expression.ALLOW_MOD_ITERATED = bool(self.exp_mod_iterated)
    self.debug_reprove = getattr(options, "debug_reprove", False)
    self.compute_steps = options.compute_steps
    self.verbose = options.verbose_prover  # Step-by-step state printing
    self.print_new_rules = getattr(options, "print_rules", False)
    self.verbose_prefix = verbose_prefix
    # Memory of past stripped configurations with enough extra information to
    # try to prove rules. Set to None to disable proving new rules (for example
    # if this is a recursive proof system being used simply to apply rules).
    self.past_configs = defaultdict(Past_Config)
    # Collection of proven rules indexed by stripped configurations.
    self.rules = {}
    # Distance-indexed dictionary for limited rules:
    # (state, dir) -> {(left_dist, right_dist): {(sub_left, sub_right): [rules]}}
    self.limited_rules = {}
    # Canonical rule signature -> existing Rule, for deduplication.
    self._rule_signatures = {}
    # (stripped_config, delta_loop) -> self.num_rules when a rule was proven,
    # to avoid redundant re-proving when no new subrules have been learned.
    self._proven_delta_loops = {}

    # Stats
    self.num_rules = 0
    self.num_duplicate_rules = 0
    self.num_rules_by_level = defaultdict(int)  # Count of rules proven at each level.
    self.num_meta_diff_rules = 0  # Backward compat: Diff_Rules at level > 1.
    self.num_linear_rules = 0
    self.num_finite_linear_rules = 0
    # Number of rules with an exponent that decreases by > 1 and thus
    # could lead to collatz-like behavior.
    self.num_collatz_rules = 0
    self.num_failed_proofs = 0
    self.num_loops = 0
    self.last_prove_fail_reason = None
    # Tracks the highest level of any rule applied during the current inner
    # simulation (used only by frozen inner provers in prove_rule).
    self.max_rule_level_used = 0
    self.last_rule_var_info = None
    # TODO: Record how many steps are taken by recursive rules in simulator.

  def print_this(self, *args):
    """Print with prefix."""
    print(self.verbose_prefix, end=" ")
    for arg in args:
      print(arg, end=" ")
    print()

  def _print_new_rule(self, rule):
    print()
    print("New Rule:")
    for line in str(rule).splitlines():
      print("  " + line)

  def print_rules(self, args=None):
    all_rules = {}
    for val in self.rules.values():
      if isinstance(val, list):
        for rule in val:
          all_rules[rule.num] = rule
      else:
        all_rules[val.num] = val

    found_rule = False
    for _, rule in sorted(all_rules.items()):
      if args is not None and str(rule.num) != str(args):
        continue
      found_rule = True
      print()
      for line in str(rule).splitlines():
        self.print_this(line)
      self.print_this("Num uses:", rule.num_uses)

    if found_rule:
      print()

  def _can_use_in_meta_rule(self, rule) -> bool:
    if self.prover_level < ProverLevel.EXP:
      return False
    if isinstance(rule, Iterated_Rule):
      if self.prover_level < ProverLevel.ITERATED:
        return False
      if rule.has_collatz_decrease:
        return False
    elif isinstance(rule, Diff_Rule):
      if rule.has_collatz_decrease:
        return False
    return True

  def _matching_rules_for_config(self, stripped_config):
    matching = []
    if self.options.limited_rules:
      (state, dir, stripped_tape_left, stripped_tape_right) = stripped_config
      by_dist = self.limited_rules.get((state, dir))
      if by_dist:
        len_l = len(stripped_tape_left)
        len_r = len(stripped_tape_right)
        for (ld, rd), sub_table in by_dist.items():
          if len_l >= ld and len_r >= rd:
            sub_left = _slice_tape_tail(stripped_tape_left, ld)
            sub_right = _slice_tape_tail(stripped_tape_right, rd)
            rules = sub_table.get((sub_left, sub_right))
            if rules:
              matching.extend(rules)
    if stripped_config in self.rules:
      matching.extend(self.rules[stripped_config])
    if len(matching) > 1:
      matching.sort(key=self._rule_priority, reverse=True)
    return matching

  def log_and_apply(self, tape, state, loop_num, remaining_loops=None, allow_log=True):
    """
    Log this configuration into the memory and check if it is similar to a
    past one. Apply rule if possible.
    """
    # Stores state, direction pointed, and list of symbols on tape.
    # Note: we ignore the number of repetitions of these sequences so that we
    #   can get a very general view of the tape.
    stripped_config = strip_config(state, tape.dir, tape.tape)
    full_config = (state, tape, loop_num)

    # Log into past_configs and try to prove a new rule if it has recurred
    # 3 times in arithmetic progression.
    if self.past_configs is not None and not self.frozen and allow_log:
      past_config = self.past_configs[stripped_config]
      if past_config.log_config(loop_num):
        # We see enough of a pattern to try and prove a rule.
        delta_loop = loop_num - past_config.last_loop_num

        # Avoid wasted re-proving if an existing rule already applies and either
        # cannot be wrapped in a meta-rule (e.g. Collatz rule) or was already
        # proven for this (stripped_config, delta_loop) with no new rules since.
        already_proven_same = self._proven_delta_loops.get((stripped_config, delta_loop)) == self.num_rules
        existing = self._matching_rules_for_config(stripped_config)
        if existing:
          preferred = existing if already_proven_same else [r for r in existing if not self._can_use_in_meta_rule(r)]
          if preferred:
            res = self._apply_rule_list(preferred, full_config)
            if res and res.condition != NOTHING_TO_DO:
              return res

        if remaining_loops is not None and delta_loop > remaining_loops:
          return ProverResult(OVER_LOOPS, delta_loop=delta_loop, remaining_loops=remaining_loops)
        rule = self.prove_rule(stripped_config, full_config, delta_loop)
        if not rule:
          self.num_failed_proofs += 1
        else:
          rule = self.add_rule(rule, stripped_config)
          self._proven_delta_loops[(stripped_config, delta_loop)] = self.num_rules

          # Try to apply transition
          is_good, res = self.apply_rule(rule, full_config)
          if is_good:
            result, _ = res
            rule.num_uses += 1
            assert isinstance(result, ProverResult), result
            return result
      elif len(self.past_configs) > self.options.max_prover_configs:
        self.past_configs.clear()

    # Otherwise (or if proving failed), try to apply an already proven rule.
    result = self.try_apply_a_rule(stripped_config, full_config)
    if result:
      return result

    return ProverResult(NOTHING_TO_DO)

  def _apply_rule_list(self, rules, full_config):
    """Try candidate rules in priority order and apply the first one that matches."""
    has_below_min = False
    for rule in rules:
      is_good, res = self.apply_rule(rule, full_config)
      if is_good:
        result, large_delta = res
        self.max_rule_level_used = max(self.max_rule_level_used, rule.level)
        # Optimization: If we apply a rule and we are not trying to perform
        # recursive proofs, clear past configuration memory.
        # Likewise, even normal recursive proofs cannot use every subrule
        # as a step (e.g. rules with large negative deltas).
        if self.prover_level < ProverLevel.EXP or large_delta:
          if self.past_configs is not None:
            self.past_configs.clear()
        rule.num_uses += 1
        assert isinstance(result, ProverResult), result
        return result
      # TODO: When running inside prove_rule (frozen prover), surface CONST_MISMATCH / UNPROVEN_PARITY
      # back to prove_rule so it can specialize variables using the concrete value (x = 0 or parity)
      # and apply the exact same subrules as concrete simulation.
      if res not in (UNPROVEN_PARITY, CONST_MISMATCH):
        has_below_min = True

    if has_below_min:
      return ProverResult(NOTHING_TO_DO)
    return None

  def try_apply_a_rule(self, stripped_config, full_config):
    if self.options.limited_rules:
      result = self.try_apply_a_limited_rule(stripped_config, full_config)
      if result:
        return result
    if stripped_config in self.rules:
      return self._apply_rule_list(self.rules[stripped_config], full_config)

  @staticmethod
  def _rule_priority(rule):
    return (rule.level, rule.num)

  def try_apply_a_limited_rule(self, stripped_config, full_config):
    (state, dir, stripped_tape_left, stripped_tape_right) = stripped_config
    by_dist = self.limited_rules.get((state, dir))
    if not by_dist:
      return None

    len_l = len(stripped_tape_left)
    len_r = len(stripped_tape_right)
    matching_rules = []

    for (ld, rd), sub_table in by_dist.items():
      if len_l >= ld and len_r >= rd:
        sub_left = _slice_tape_tail(stripped_tape_left, ld)
        sub_right = _slice_tape_tail(stripped_tape_right, rd)
        rules = sub_table.get((sub_left, sub_right))
        if rules:
          matching_rules.extend(rules)

    if not matching_rules:
      return None

    # Prioritize higher level rules first, then later proven rules first.
    if len(matching_rules) > 1:
      matching_rules.sort(key=self._rule_priority, reverse=True)

    return self._apply_rule_list(matching_rules, full_config)

  def add_rule(self, rule, stripped_config):
    """Add a proven rule, deduplicating against existing rules. Returns the stored rule."""
    sig = _rule_signature(rule)
    if sig in self._rule_signatures:
      existing = self._rule_signatures[sig]
      self.num_duplicate_rules += 1
      if self.verbose or self.print_new_rules:
        print(f"\nDuplicate Rule (matches Rule {existing.num}) — not added.")
      return existing
    self._rule_signatures[sig] = rule

    zero_slots = _rule_zero_min_slots(rule)
    # Remember rule.
    if rule.is_limited:
      (state, dir, stripped_tape_left, stripped_tape_right) = stripped_config
      sub_left = _slice_tape_tail(stripped_tape_left, rule.left_dist)
      sub_right = _slice_tape_tail(stripped_tape_right, rule.right_dist)
      dist_key = (rule.left_dist, rule.right_dist)

      by_dist = self.limited_rules.setdefault((state, dir), {})
      by_sub = by_dist.setdefault(dist_key, {})
      rule_list = by_sub.setdefault((sub_left, sub_right), [])
      rule_list.append(rule)
      rule_list.sort(key=self._rule_priority, reverse=True)

      # Also register variant keys where a 0-minimum block is missing from the tape.
      for slot_dir, slot_idx, _ in zero_slots:
        if slot_dir == 0 and rule.left_dist > 0:
          alt_dist = (rule.left_dist - 1, rule.right_dist)
          alt_sub = (_remove_tuple_at(sub_left, slot_idx), sub_right)
        elif slot_dir == 1 and rule.right_dist > 0:
          alt_dist = (rule.left_dist, rule.right_dist - 1)
          alt_sub = (sub_left, _remove_tuple_at(sub_right, slot_idx))
        else:
          continue
        alt_by_sub = by_dist.setdefault(alt_dist, {})
        alt_list = alt_by_sub.setdefault(alt_sub, [])
        if rule not in alt_list:
          alt_list.append(rule)
          alt_list.sort(key=self._rule_priority, reverse=True)

      self.rules[rule.num] = rule
    else:
      rule_list = self.rules.setdefault(stripped_config, [])
      rule_list.append(rule)
      rule_list.sort(key=self._rule_priority, reverse=True)

      (state, dir, stripped_tape_left, stripped_tape_right) = stripped_config
      for slot_dir, slot_idx, _ in zero_slots:
        if slot_dir == 0:
          alt_stripped = (state, dir, _remove_tuple_at(stripped_tape_left, slot_idx), stripped_tape_right)
        else:
          alt_stripped = (state, dir, stripped_tape_left, _remove_tuple_at(stripped_tape_right, slot_idx))
        alt_list = self.rules.setdefault(alt_stripped, [])
        if rule not in alt_list:
          alt_list.append(rule)
          alt_list.sort(key=self._rule_priority, reverse=True)

    self.num_rules += 1
    self.num_rules_by_level[rule.level] += 1
    if isinstance(rule, Diff_Rule):
      if rule.level > 1:
        self.num_meta_diff_rules += 1
      if rule.has_collatz_decrease:
        self.num_collatz_rules += 1
    elif isinstance(rule, Iterated_Rule):
      self.num_linear_rules += 1
      if not rule.infinite:
        self.num_finite_linear_rules += 1
      if rule.has_collatz_decrease:
        self.num_collatz_rules += 1

    # Clear our memory. We cannot use it for future rules because the
    # number of steps will be wrong now that we have proven this rule.
    #
    # Note: We save the past_config for this stripped_config so that
    # information for Collatz rules is not lost.
    saved = self.past_configs[stripped_config]
    self.past_configs.clear()
    saved.last_loop_num = None
    self.past_configs[stripped_config] = saved
    return rule

  def prove_rule(self, stripped_config, full_config, delta_loop, const_blocks=None):
    """Try to prove a general rule based upon specific example.

    Returns rule if successful or None.
    """
    try:
      return self._prove_rule(stripped_config, full_config, delta_loop, const_blocks=const_blocks)
    except NotImplementedError as e:
      self.last_prove_fail_reason = str(e)
      if self.verbose:
        print()
        self.print_this(f"[PROVER FAILURE] {e}")
        print()
      return None

  def _prove_rule(self, stripped_config, full_config, delta_loop, const_blocks=None):
    # Unpack configurations
    new_state, new_tape, new_loop_num = full_config
    self.last_prove_fail_reason = None

    if self.verbose:
      print()
      self.print_this("** Testing new rule **")
      self.print_this("Original config:", new_tape.print_with_state(new_state))
      self.print_this("Start loop:", new_loop_num, "Loops:", delta_loop)

    # Create the limited simulator with limited or no prover.
    new_options = copy.copy(self.options)
    new_options.max_loops = 0
    new_options.prover_level = ProverLevel.NONE  # We'll create our own prover if needed.
    new_options.verbose_prover = False
    new_options.print_rules = False
    new_options.verbose_simulator = self.verbose
    gen_sim = Simulator.Simulator(
      self.machine,
      new_options,
      init_tape=False,
      verbose_prefix=self.verbose_prefix + "  ",
      is_base_simulator=False,
    )
    gen_sim.state = new_state
    gen_sim.step_num = ConstantToExpression(0)

    # If prover can run recursively, we let it simulate with a lazy prover.
    # That is, one that cannot prove new rules, only use already proven ones.
    if self.prover_level >= ProverLevel.EXP:
      gen_sim.prover = copy.copy(self)
      gen_sim.prover.frozen = True
      gen_sim.prover.past_configs = None
      gen_sim.prover.max_rule_level_used = 0
      gen_sim.prover.last_rule_var_info = None
      gen_sim.prover.verbose_prefix = gen_sim.verbose_prefix + "  "

    # Create a new tape which we will use to simulate general situation.
    const_blocks = const_blocks or set()
    capped_vars = set()
    saw_multi_vars = False
    gen_sim.tape = new_tape.copy()
    # Minimum value reached by Algebraic_Expression exponents containing each variable:
    # - Without --exp-zero-exponents: min between full steps (kept >= 1 via offset=1).
    # - With --exp-zero-exponents: sub-transition min (also decremented by 1 on macro
    #   moves to reflect popping before pushing), allowing exponents to reach >= 0
    #   unless the block never drops below its initial value and !can_start_at_zero.
    min_val = {}
    can_start_at_zero = {}  # Whether variable is only ever consumed by chain moves.
    init_var_pos = {}
    for direction in range(2):
      for i, block in enumerate(gen_sim.tape.tape[direction]):
        # Generalize, eg. (abc)^5 -> (abc)^(n+5)
        # Blocks with one rep or explicitly pinned in const_blocks stay constant.
        if not block.num.is_inf and block.num != 1 and (direction, i) not in const_blocks:
          x = Variable()
          init_count = Exp_Int.try_eval(block.num)
          # Avoid proving rules with ridiculously huge initial values (like ExpInt).
          if init_count is None or init_count > 2**20:
            init_count = 2**20
            assert block.num > init_count, block.num
            capped_vars.add(x)
          assert isinstance(init_count, int)
          x_init = VarPlusConstExpression(x, init_count)
          block.num = x_init
          min_val[x] = block.num.const
          init_var_pos[x] = (direction, i)
          left_sym = gen_sim.tape.tape[direction][i - 1].symbol if i > 0 else None
          if i + 1 < len(gen_sim.tape.tape[direction]):
            right_sym = gen_sim.tape.tape[direction][i + 1].symbol
          else:
            right_sym = None  # Adjacent to head
          can_start_at_zero[x] = left_sym != right_sym
    initial_tape = gen_sim.tape.copy()
    gen_sim.dir = gen_sim.tape.dir
    gen_sim.init_touch_tracking()

    initial_len = {
      LEFT: len(initial_tape.tape[LEFT]),
      RIGHT: len(initial_tape.tape[RIGHT]),
    }
    # Run the simulator
    gen_sim.verbose_print()
    while gen_sim.num_loops < delta_loop:
      block = gen_sim.tape.get_top_block()
      while ae.min_val(block.num) <= 0:
        # This corresponds to a block which looks like (abc)^(n+0).
        # With --exp-const-blocks (enabled by default), try forcing n = 0 by pinning the block
        # as constant from the start and reproving so any resulting block merges happen in sync.
        block_vars = variables(block.num)
        if getattr(self.options, "exp_const_blocks", True) and len(block_vars) == 1:
          x = next(iter(block_vars))
          if x not in capped_vars and _subst_var_zero(block.num, {x: ConstantToExpression(0)}) == 0:
            if self.verbose:
              self.print_this(
                f"[PROVER] Reproving with constant block {init_var_pos[x]} ({x} = 0) at loop {gen_sim.num_loops}"
              )
            return self._prove_rule(
              stripped_config,
              full_config,
              delta_loop,
              const_blocks=const_blocks | {init_var_pos[x]},
            )
        self.last_prove_fail_reason = "Exponent below min"
        if self.verbose:
          print()
          self.print_this("[PROVER FAILURE] Exponent below min **")
          self.print_this(gen_sim.tape.print_with_state(gen_sim.state))
          print()
        return None

      prev_top_vars = variables(block.num)
      prev_top_var = next(iter(prev_top_vars)) if len(prev_top_vars) == 1 else None
      prev_top_is_ae = prev_top_var is not None and isinstance(block.num, Algebraic_Expression)
      prev_top_min = _ae_min_for_var(block.num, prev_top_var) if prev_top_is_ae else None
      # Sub-transition min after popping 1 symbol (before pushing), used for macro moves.
      prev_top_sub_min = _ae_min_for_var(block.num, prev_top_var, delta=-1) if prev_top_is_ae else None
      prev_num_rule_moves = gen_sim.num_rule_moves
      prev_num_macro_moves = gen_sim.num_macro_moves
      prev_num_chain_moves = gen_sim.num_chain_moves

      # TODO: Specialize variables using concrete values (x = 0 or parity) if a recursive rule inside
      # gen_sim misses with CONST_MISMATCH or UNPROVEN_PARITY, so gen_sim mirrors concrete simulation.
      gen_sim.step()
      self.num_loops += 1

      if gen_sim.op_state is not Turing_Machine.RUNNING:
        self.last_prove_fail_reason = f"Machine stopped running: {gen_sim.op_state}"
        if self.verbose:
          print()
          self.print_this("[PROVER FAILURE] Machine stopped running:", gen_sim.op_state)
          print()
        return None

      if gen_sim.num_rule_moves > prev_num_rule_moves and gen_sim.prover and gen_sim.prover.last_rule_var_info:
        for v, (req_cur_min, is_lim, req_min) in gen_sim.prover.last_rule_var_info.items():
          if v in min_val:
            if not is_lim and req_min > 0 and req_cur_min - 1 < min_val[v]:
              can_start_at_zero[v] = False
            if req_cur_min < min_val[v]:
              min_val[v] = req_cur_min
        gen_sim.prover.last_rule_var_info = None
      if gen_sim.num_macro_moves > prev_num_macro_moves:
        for v in prev_top_vars:
          can_start_at_zero[v] = False
        if self.exp_zero_exponents and prev_top_var in min_val and prev_top_sub_min is not None:
          min_val[prev_top_var] = min(min_val[prev_top_var], prev_top_sub_min)
      elif gen_sim.num_chain_moves > prev_num_chain_moves and prev_top_var in can_start_at_zero:
        if prev_top_min is not None and prev_top_min < min_val[prev_top_var]:
          can_start_at_zero[prev_top_var] = False

      # Update min_val for each expression.
      # TODO: We only need to update for the blocks on each side of head.
      # TODO: Better yet, build these checks into the data type!
      for dir in range(2):
        for block in gen_sim.tape.tape[dir]:
          vars = variables(block.num)
          if len(vars) > 1:
            # Allow simulation to continue; we'll recover at the end if the extra
            # variables come from blocks that end up as constants.
            saw_multi_vars = True
            cur_min = ae.min_val(block.num)
            for x in vars:
              if x in min_val and cur_min < min_val[x]:
                min_val[x] = cur_min
          elif len(vars) == 1 and isinstance(block.num, Algebraic_Expression):
            x = list(vars)[0]
            cur_min = _ae_min_for_var(block.num, x)
            if cur_min < min_val[x]:
              min_val[x] = cur_min

    # Make sure finishing tape has the same stripped config as original.
    gen_stripped_config = strip_config(gen_sim.state, gen_sim.tape.dir, gen_sim.tape.tape)
    if gen_stripped_config != stripped_config:
      if getattr(self.options, "exp_const_blocks", True):
        new_const_blocks = set(const_blocks)
        for dir in range(2):
          for block in gen_sim.tape.tape[dir]:
            block_vars = variables(block.num)
            if len(block_vars) == 1:
              x = next(iter(block_vars))
              if (
                x in init_var_pos
                and x not in capped_vars
                and _subst_var_zero(block.num, {x: ConstantToExpression(0)}) == 0
              ):
                new_const_blocks.add(init_var_pos[x])
        if new_const_blocks != const_blocks:
          if self.verbose:
            self.print_this(f"[PROVER] Reproving with constant blocks {sorted(new_const_blocks)} after config mismatch")
          return self._prove_rule(stripped_config, full_config, delta_loop, const_blocks=new_const_blocks)
      self.last_prove_fail_reason = "Config mismatch"
      if self.verbose:
        print()
        self.print_this("[PROVER FAILURE] Config mismatch **")
        self.print_this(gen_sim.tape)
        self.print_this(gen_stripped_config)
        self.print_this(stripped_config)
        print()
      return None

    if saw_multi_vars:
      # Any initial variable block whose final exponent became constant must start at
      # that constant for the rule to be repeatable. Specialize its variable to 0.
      while True:
        vars_to_zero = []
        for dir in range(2):
          for init_block, final_block in zip(initial_tape.tape[dir], gen_sim.tape.tape[dir]):
            if isinstance(init_block.num, Algebraic_Expression) and is_const(final_block.num):
              x = init_block.num.variable_restricted()
              if x not in capped_vars and x not in vars_to_zero:
                vars_to_zero.append(x)
        if not vars_to_zero:
          break
        for x in vars_to_zero:
          if self.verbose:
            self.print_this(f"[PROVER] Specializing {x} = 0 after multiple vars in one term")
          _specialize_var_zero(x, initial_tape, gen_sim, min_val)
          can_start_at_zero.pop(x, None)
      if any(len(variables(block.num)) > 1 for dir in range(2) for block in gen_sim.tape.tape[dir]):
        self.last_prove_fail_reason = "Multiple vars in one term"
        if self.verbose:
          print()
          self.print_this("[PROVER FAILURE] Multiple vars in one term **")
          self.print_this(gen_sim.tape)
          print()
        return None

    # Compute the rule level: 1 + the highest level of any rule used in the proof.
    # Level 1 = proven from raw simulation; Level N = uses Level N-1 rules in proof.
    if self.prover_level >= ProverLevel.EXP:
      rule_level = gen_sim.prover.max_rule_level_used + 1
    else:
      rule_level = 1

    # Compute the number of initial blocks touched on each side of the tape.
    for dir in range(2):
      prefix = gen_sim.min_untouched_prefix[dir]
      assert prefix >= 0, prefix
      assert gen_sim.tape.tape[dir][:prefix] == initial_tape.tape[dir][:prefix], (
        dir,
        prefix,
        gen_sim.tape.tape[dir],
        initial_tape.tape[dir],
      )
    left_dist = initial_len[LEFT] - gen_sim.min_untouched_prefix[LEFT]
    right_dist = initial_len[RIGHT] - gen_sim.min_untouched_prefix[RIGHT]

    if self.options.limited_rules:
      initial_tape.tape[0] = _slice_tape_tail(initial_tape.tape[0], left_dist)
      initial_tape.tape[1] = _slice_tape_tail(initial_tape.tape[1], right_dist)
      gen_sim.tape.tape[0] = _slice_tape_tail(gen_sim.tape.tape[0], left_dist)
      gen_sim.tape.tape[1] = _slice_tape_tail(gen_sim.tape.tape[1], right_dist)

    # If machine has run delta_steps without error, it is a general rule.
    # Compute the diff_tape and figure out if it's a Diff_Rule.
    is_diff_rule = True
    # diff_tape = new_tape.copy()
    diff_tape = gen_sim.tape.copy()
    for dir in range(2):
      for diff_block, initial_block in zip(diff_tape.tape[dir], initial_tape.tape[dir]):
        if not diff_block.num.is_inf:
          diff_block.num -= initial_block.num
          if isinstance(diff_block.num, Algebraic_Expression) and diff_block.num.is_const:
            diff_block.num = diff_block.num.const
          elif not is_const(diff_block.num):
            is_diff_rule = False
          if not isinstance(initial_block.num, Algebraic_Expression) and diff_block.num != 0:
            # Fixed constant block changed value; cannot be repeated at all.
            self.last_prove_fail_reason = CONST_MISMATCH
            if self.verbose:
              print()
              self.print_this("[PROVER FAILURE] Constant block changed value **")
              self.print_this("Initial:", initial_tape)
              self.print_this("Result:", gen_sim.tape)
              print()
            return None

    if not is_diff_rule:
      # TODO: Don't do all the work above if we're not going to use it
      # Get everything in the right form for an Iterated_Rule.
      var_list = []
      min_list = []
      assignment = {}
      new_const_blocks = set(const_blocks)
      for init_block in initial_tape.tape[0] + initial_tape.tape[1]:
        if isinstance(init_block.num, Algebraic_Expression):
          x = init_block.num.variable_restricted()
          if isinstance(min_val[x], float) and math.isinf(min_val[x]):
            if getattr(self.options, "exp_const_blocks", True) and x in init_var_pos:
              new_const_blocks.add(init_var_pos[x])
              continue
            self.last_prove_fail_reason = "Unbounded negative min_val"
            return None
          var_list.append(x)
          allow_zero = self.exp_zero_exponents and (
            min_val[x] < init_block.num.const or can_start_at_zero.get(x, False)
          )
          req_min = init_block.num.const - min_val[x] + (0 if allow_zero else 1)
          if req_min > init_block.num.const and x in init_var_pos:
            new_const_blocks.add(init_var_pos[x])
          min_list.append(req_min)
          # Hackish: If exponent was x + 5 we want to replace all x with x - 5.
          # TODO: Make nicer.
          assignment[x] = init_block.num - 2 * init_block.num.const
        else:
          var_list.append(None)
          min_list.append(init_block.num)

      if getattr(self.options, "exp_const_blocks", True) and new_const_blocks != const_blocks:
        if self.verbose:
          self.print_this(f"[PROVER] Reproving with constant blocks {sorted(new_const_blocks)} (min_val reached 0)")
        return self._prove_rule(stripped_config, full_config, delta_loop, const_blocks=new_const_blocks)

      # TODO: result_list = []
      result_tape = gen_sim.tape
      # Fix up result_tape to by applying variable substitution.
      for result_block in result_tape.tape[0] + result_tape.tape[1]:
        result_block.num = substitute(result_block.num, assignment)

      # Fix num_steps.
      if self.compute_steps and gen_sim.compute_steps:
        num_steps = substitute(gen_sim.step_num, assignment)
        states_last_seen = {
          state: substitute(last_seen, assignment) for state, last_seen in gen_sim.states_last_seen.items()
        }
      else:
        num_steps = None
        states_last_seen = None

      # Figure out if this is a Iterated_Rule
      rule, lin_err = Iterated_Rule.try_gen(
        var_list,
        min_list,
        result_tape,
        num_steps,
        gen_sim.num_loops,
        self.num_rules,
        states_last_seen,
        rule_level,
        initial_state=new_state,
      )
      if not rule:
        composed = _try_compose_permutation_rule(var_list, min_list, result_tape)
        if composed is not None:
          comp_min_list, comp_tape, perm_order = composed
          rule, lin_err = Iterated_Rule.try_gen(
            var_list,
            comp_min_list,
            comp_tape,
            None,
            gen_sim.num_loops * perm_order,
            self.num_rules,
            states_last_seen,
            rule_level,
            initial_state=new_state,
          )
      if rule:
        if self.options.limited_rules:
          rule.make_limited(left_dist, right_dist)

        if (self.verbose or self.print_new_rules) and _rule_signature(rule) not in self._rule_signatures:
          self._print_new_rule(rule)

      if not rule:
        if self.verbose:
          self.print_this(f"[PROVER FAILURE] Iterated_Rule generation failed: {lin_err}")
        return None

      if self.debug_reprove:
        self._debug_reprove_rule(rule, full_config)

      return rule

    else:  # Diff Rule
      assert is_diff_rule
      # Tighten up rule to be as general as possible
      # (e.g. by replacing x+5 with x+1 if the rule holds for 1).
      replaces = {}
      new_const_blocks = set(const_blocks)
      for dir in range(2):
        for init_block in initial_tape.tape[dir]:
          if isinstance(init_block.num, Algebraic_Expression):
            x = init_block.num.variable_restricted()
            if isinstance(min_val[x], float) and math.isinf(min_val[x]):
              if getattr(self.options, "exp_const_blocks", True) and x in init_var_pos:
                new_const_blocks.add(init_var_pos[x])
                continue
              self.last_prove_fail_reason = "Unbounded negative min_val"
              return None
            allow_zero = self.exp_zero_exponents and (
              min_val[x] < init_block.num.const or can_start_at_zero.get(x, False)
            )
            offset = 0 if allow_zero else 1
            if min_val[x] - offset < 0 and x in init_var_pos:
              new_const_blocks.add(init_var_pos[x])
            new_value = VariableToExpression(x) - min_val[x] + offset
            init_block.num = init_block.num.substitute({x: new_value})
            replaces[x] = new_value
          else:
            assert is_const(init_block.num), init_block
      if getattr(self.options, "exp_const_blocks", True) and new_const_blocks != const_blocks:
        if self.verbose:
          self.print_this(f"[PROVER] Reproving with constant blocks {sorted(new_const_blocks)} (min_val reached 0)")
        return self._prove_rule(stripped_config, full_config, delta_loop, const_blocks=new_const_blocks)
      # Fix diff_tape (needed for recursive meta diff rules).
      for dir in range(2):
        for diff_block in diff_tape.tape[dir]:
          diff_block.num = substitute(diff_block.num, replaces)
      # Fix num_steps.
      if self.compute_steps and gen_sim.compute_steps:
        num_steps = substitute(gen_sim.step_num, replaces)
        states_last_seen = {
          state: substitute(last_seen, replaces) for state, last_seen in gen_sim.states_last_seen.items()
        }
      else:
        num_steps = None
        states_last_seen = None

      # Cast num_steps as an Algebraic Expression (if it somehow got through
      # as simply an int)
      if num_steps is not None and not isinstance(num_steps, Algebraic_Expression):
        num_steps = ConstantToExpression(num_steps)

      rule = Diff_Rule(
        initial_tape,
        diff_tape,
        new_state,
        num_steps,
        gen_sim.num_loops,
        self.num_rules,
        rule_level,
        states_last_seen=states_last_seen,
        left_dist=left_dist if self.options.limited_rules else None,
        right_dist=right_dist if self.options.limited_rules else None,
      )

      if (self.verbose or self.print_new_rules) and _rule_signature(rule) not in self._rule_signatures:
        self._print_new_rule(rule)

      if self.debug_reprove:
        self._debug_reprove_rule(rule, full_config)

      return rule

  def _debug_reprove_rule(self, rule, full_config):
    """Verify a newly proven rule by simulating it from its tightest minimum exponents."""
    start_state, start_tape, _ = full_config
    tight_tape = start_tape.copy()
    expected_tape = start_tape.copy()

    expected_state = start_state
    if isinstance(rule, Diff_Rule):
      for dir in range(2):
        init_blocks = rule.initial_tape.tape[dir]
        diff_blocks = rule.diff_tape.tape[dir]
        offset = len(tight_tape.tape[dir]) - len(init_blocks)
        assert offset >= 0, (len(tight_tape.tape[dir]), len(init_blocks))
        for j, (init_b, diff_b) in enumerate(zip(init_blocks, diff_blocks)):
          idx = offset + j
          if isinstance(init_b.num, Algebraic_Expression) and not init_b.num.is_const:
            in_n = VariableToExpression(Variable()) + init_b.num.const
          else:
            in_n = init_b.num
          tight_tape.tape[dir][idx].num = in_n
          expected_tape.tape[dir][idx].num = in_n + diff_b.num
    else:
      left_len = rule.left_dist if rule.is_limited else len(start_tape.tape[0])
      right_len = rule.right_dist if rule.is_limited else len(start_tape.tape[1])
      assert len(rule.min_list) == left_len + right_len
      in_exprs = [
        VariableToExpression(Variable()) + m if v is not None else m for v, m in zip(rule.var_list, rule.min_list)
      ]
      subs = {v: expr for v, expr in zip(rule.var_list, in_exprs) if v is not None}
      for i in range(len(rule.min_list)):
        dir = 0 if i < left_len else 1
        j = i if i < left_len else i - left_len
        idx = (len(tight_tape.tape[dir]) - (left_len if dir == 0 else right_len)) + j
        in_n = in_exprs[i]
        tight_tape.tape[dir][idx].num = in_n
        if isinstance(rule, Iterated_Rule):
          func = rule.func_list[i]
          if isinstance(func, Rule_Func.Iterated_Func):
            out_n = substitute(func.step_expr, {func.var: in_n})
          elif func:
            out_n = func.apply_rep(in_n, 1)
          else:
            out_n = in_n
        else:
          out_n = substitute(rule.result_list[i], subs)
          if isinstance(out_n, Algebraic_Expression) and out_n.is_const:
            out_n = out_n.const
        if not isinstance(out_n, int) and not getattr(out_n, "is_inf", False):
          eval_n = Exp_Int.try_eval(out_n)
          if eval_n is not None:
            out_n = eval_n
        expected_tape.tape[dir][idx].num = out_n

    save_len = [
      len(start_tape.tape[0]) - rule.left_dist if rule.is_limited else 0,
      len(start_tape.tape[1]) - rule.right_dist if rule.is_limited else 0,
    ]
    for dir in range(2):
      if save_len[dir] > 0:
        sentinel = type(tight_tape.tape[dir][0])(-1, tight_tape.tape[dir][0].num)
        tight_tape.tape[dir] = [sentinel] + tight_tape.tape[dir][save_len[dir] :]
        expected_tape.tape[dir] = [sentinel.copy()] + expected_tape.tape[dir][save_len[dir] :]
      tight_tape.tape[dir] = _normalize_half_tape(tight_tape.tape[dir])
      expected_tape.tape[dir] = _normalize_half_tape(expected_tape.tape[dir])

    if self.verbose:
      print()
      self.print_this("** Reproving rule **")
      self.print_this("Start config:", tight_tape.print_with_state(start_state))
      self.print_this("Expected config:", expected_tape.print_with_state(expected_state))
      self.print_this("Loops:", rule.num_loops)

    check_options = copy.copy(self.options)
    check_options.max_loops = 0
    check_options.prover_level = ProverLevel.NONE
    check_options.verbose_prover = False
    check_options.print_rules = False
    check_options.verbose_simulator = self.verbose
    check_sim = Simulator.Simulator(
      self.machine,
      check_options,
      init_tape=False,
      verbose_prefix=self.verbose_prefix + "  ",
      is_base_simulator=False,
    )
    check_sim.tape = tight_tape
    check_sim.state = start_state
    check_sim.dir = tight_tape.dir
    if self.prover_level >= ProverLevel.EXP:
      check_sim.prover = copy.copy(self)
      check_sim.prover.frozen = True
      check_sim.prover.past_configs = None
      check_sim.prover.verbose_prefix = check_sim.verbose_prefix + "  "
      check_sim.prover.debug_reprove = False
    else:
      check_sim.prover = None

    check_sim.verbose_print()
    while check_sim.op_state is Turing_Machine.RUNNING and check_sim.num_loops < rule.num_loops:
      if check_sim.tape.get_top_symbol() == -1:
        raise AssertionError(
          f"--debug-reprove failed for rule {rule.num} (loops={check_sim.num_loops}/{rule.num_loops}): "
          f"touched outside limited region\n{rule}"
        )
      check_sim.step()

    if (
      check_sim.op_state is Turing_Machine.RUNNING
      and check_sim.num_loops == rule.num_loops
      and check_sim.state == expected_state
      and check_sim.dir == expected_tape.dir
      and _tapes_equal(check_sim.tape, expected_tape)
    ):
      if self.verbose:
        self.print_this("** Reprove succeeded **")
      return

    raise AssertionError(
      f"--debug-reprove failed for rule {rule.num} (state={check_sim.op_state}, "
      f"loops={check_sim.num_loops}/{rule.num_loops}):\n"
      f"Rule:\n{rule}\n"
      f"Expected: {expected_tape.print_with_state(expected_state)}\n"
      f"Got:      {check_sim.tape.print_with_state(check_sim.state)}"
    )

  def apply_rule(self, rule, start_config):
    """Try to apply a rule to a given configuration."""
    start_state, start_tape, start_loop_num = start_config
    if self.verbose:
      print()
      self.print_this("++ Applying Rule ++")
      self.print_this("Loop:", start_loop_num, "Rule ID:", rule.num)
      self.print_this("Rule:", str(rule).replace("\n", "\n" + self.verbose_prefix + "       "))
      self.print_this("Config:", start_tape.print_with_state(start_state))

    if rule.is_limited or _rule_zero_min_slots(rule):
      prepared_tape, save_left, save_right, eff_left_dist, eff_right_dist = _prepare_tape_for_rule(rule, start_tape)
      start_config = (start_state, prepared_tape, start_loop_num)

    if isinstance(rule, Diff_Rule):
      apply_fn = self.apply_diff_rule
    elif isinstance(rule, Iterated_Rule):
      apply_fn = self.apply_linear_rule
    else:
      raise NotImplementedError(f"Cannot apply rule of type {type(rule)}")

    try:
      success, other = apply_fn(rule, start_config)
    except NotImplementedError as e:
      if self.verbose:
        self.print_this(f"++ Rule cannot apply: {e}")
      return False, None

    if rule.is_limited and success:
      prover_result, large_delta = other
      if prover_result.condition == APPLY_RULE:
        # If we are applying this rule, add back on the saved part of the
        # tape that was not part of this limited rule.
        prover_result.new_tape.tape[0], prover_result.left_dist = _splice_limited_half_tape(
          save_left, prover_result.new_tape.tape[0], eff_left_dist
        )
        prover_result.new_tape.tape[1], prover_result.right_dist = _splice_limited_half_tape(
          save_right, prover_result.new_tape.tape[1], eff_right_dist
        )
      return success, (prover_result, large_delta)

    return success, other

  def apply_diff_rule(self, rule, start_config):
    ## Unpack input
    new_state, new_tape, new_loop_num = start_config
    new_tape = new_tape.copy()  # Make a clean copy that we can edit here.

    ## Calculate number of repetitions allowable and other tape-based info.
    num_reps = None
    limit_dir = None
    limit_index = None
    limit_final = None

    init_value = {}
    delta_value = {}
    # large_delta == True  iff there is a negative delta != -1
    # We keep track because even recursive proofs cannot contain rules
    # with large_deltas.
    large_delta = False
    for dir in range(2):
      for i, (init_block, diff_block, new_block) in enumerate(
        zip(
          rule.initial_tape.tape[dir],
          rule.diff_tape.tape[dir],
          new_tape.tape[dir],
        )
      ):
        # The constant term in init_block.num represents the minimum
        # required value.
        if isinstance(init_block.num, Algebraic_Expression):
          # Calculate the initial and change in value for each variable.
          x = init_block.num.variable_restricted()
          # init_block.num.const == min_value for this exponent.
          init_value[x] = new_block.num - init_block.num.const
          if not always_ge(init_value[x], 0):
            if self.verbose:
              self.print_this("++ Current config is below rule minimum ++")
              self.print_this("Config block:", new_block)
              self.print_this("Rule initial block:", init_block)
              self.print_this("")
            return False, None
          delta_value[x] = Exp_Int.try_simplify(diff_block.num)
          assert isinstance(delta_value[x], (int, NatExpr)), repr(delta_value[x])
          # If this block's repetitions will be depleted during this transition,
          #   count the number of repetitions that it can allow while staying
          #   above the minimum requirement.
          if delta_value[x] < 0:
            if delta_value[x] != -1:
              large_delta = True
            if num_reps is None:
              if not is_const(init_value[x]) and delta_value[x] != -1:
                if self.verbose:
                  self.print_this("++ Collatz diff ++")
                  self.print_this("From: num_reps = (%r // %r)  + 1" % (init_value[x], -delta_value[x]))
                  self.print_this("")
                return False, None
              else:
                # First one is safe.
                # For example, if we have a rule:
                #   Initial: 0^Inf 2^(d + 1) (0) B> 2^(f + 2) 0^Inf
                #   Diff:    0^Inf 2^1 (0) B> 2^-1 0^Inf
                # then:
                #   0^Inf 2^3  (0)B> 2^(s + 11) 0^Inf
                # goes to:
                #   0^Inf 2^(s + 12)  (0)B> 2^2 0^Inf
                this_reps, this_final = Rule_Func.Subtract_Func(
                  var=x,
                  min=init_block.num.const,
                  const=-delta_value[x],
                ).max_reps(new_block.num)
                num_reps = this_reps
                limit_dir = dir
                limit_index = i
                limit_final = this_final
            else:
              if is_const(init_value[x]) and is_const(num_reps):
                this_reps, this_final = Rule_Func.Subtract_Func(
                  var=x,
                  min=init_block.num.const,
                  const=-delta_value[x],
                ).max_reps(new_block.num)
                if this_reps < num_reps:
                  num_reps = this_reps
                  limit_dir = dir
                  limit_index = i
                  limit_final = this_final
              else:
                # Example Rule:
                #   Initial: 0^Inf 2^a+1 0^1 1^b+3 B> 0^1 1^c+1 0^Inf
                #   Diff:    0^Inf 2^-1  0^0 1^+2  B> 0^0 1^-1  0^Inf
                # Applied to tape:
                #   0^Inf 2^d+5 0^1 1^3 B> 0^1 1^e+3 0^Inf
                # We should apply the rule either d+4 or e+2 times depending
                # on which is smaller. Too complicated, we fail.
                if self.verbose:
                  self.print_this("++ Multiple negative diffs for expressions ++")
                  self.print_this("Config block:", new_block)
                  self.print_this("Rule initial block:", init_block)
                  self.print_this("Rule diff block:", diff_block)
                  self.print_this("Config tape:", new_tape)
                  self.print_this("Initial tape:", rule.initial_tape)
                  self.print_this("Rule diff tape:", rule.diff_tape)
                  self.print_this("")
                return False, None
        elif getattr(init_block.num, "is_inf", False):
          if not getattr(new_block.num, "is_inf", False):
            return False, CONST_MISMATCH
        elif new_block.num != init_block.num or diff_block.num != 0:
          return False, CONST_MISMATCH

    # If none of the diffs are negative, this will repeat forever.
    if num_reps is None:
      if self.verbose:
        self.print_this("++ Rules applies infinitely ++")
        print()
      states_last_seen = None
      if rule.states_last_seen:
        states_last_seen = {state: math.inf for state in rule.states_last_seen}
      return True, (
        ProverResult(INF_REPEAT, states_last_seen=states_last_seen),
        large_delta,
      )

    # If we cannot even apply this transition once, we're done.
    if is_const(num_reps) and num_reps <= 0:
      if self.verbose:
        self.print_this("++ Rule cannot apply: Below min")
        print()
      return False, None

    ## Determine number of base steps taken by applying rule.
    if self.compute_steps:
      # Convert this to an expression of one variable (k) which represents the
      # number of steps to apply rule once (after rule has already been applied
      # k times).
      k = NewVariableExpression()
      this_num_steps = substitute(
        rule.num_steps,
        {x: init_value[x] + delta_value[x] * k for x in init_value},
      )
      diff_steps = series_sum(this_num_steps, k.variable(), num_reps)
      # Compute diff_steps until each state was last seen.
      last_value = {var: init_value[var] + delta_value[var] * (num_reps - 1) for var in init_value}
      states_last_seen = {}
      for state, last_seen in rule.states_last_seen.items():
        # After the rule is applied, how many steps before that did we last see
        # `state`.
        last_seen_ago = rule.num_steps - last_seen
        states_last_seen[state] = substitute(diff_steps - last_seen_ago, last_value)

    else:
      diff_steps = None
      states_last_seen = None

    ## Alter the tape to account for applying rule.
    self.last_rule_var_info = {}
    return_tape = new_tape.copy()
    for dir in range(2):
      for i, (init_block, diff_block, return_block) in enumerate(
        zip(rule.initial_tape.tape[dir], rule.diff_tape.tape[dir], return_tape.tape[dir])
      ):
        if not return_block.num.is_inf:
          if isinstance(init_block.num, Algebraic_Expression) and isinstance(return_block.num, Algebraic_Expression):
            in_vars = variables(return_block.num)
            if len(in_vars) == 1:
              in_var = next(iter(in_vars))
              req_min = init_block.num.const
              is_lim = dir == limit_dir and i == limit_index
              # WARNING: Checking only the input block assumes any decreasing AE block is the
              # limiting block (multiple decreasing exponents are only allowed for constants).
              # If multi-decreasing rules are ever allowed with AEs, non-limiting decreasing
              # blocks must also be checked at the start of their last iteration
              # (ae.min_val(output) - diff - req_min).
              self.last_rule_var_info[in_var] = (
                _ae_min_for_var(return_block.num, in_var, delta=-req_min + (0 if is_lim else 1)),
                is_lim,
                req_min,
              )
          if dir == limit_dir and i == limit_index:
            return_block.num = limit_final
          else:
            if diff_block.num != 0:
              try:
                return_block.num += num_reps * diff_block.num
              except TypeError:
                print(
                  f"CRASH: return_block.num={type(return_block.num)} ({return_block.num}), "
                  f"num_reps={type(num_reps)} ({num_reps}) diff_block.num={type(diff_block.num)} ({diff_block.num})"
                )
                raise
          if isinstance(return_block.num, Algebraic_Expression) and return_block.num.is_const:
            return_block.num = return_block.num.const
      return_tape.tape[dir] = _normalize_half_tape(return_tape.tape[dir])

    ## Return the pertinent info
    if self.verbose:
      self.print_this("++ Rule successfully applied ++")
      self.print_this("Times applied:", approx_str(num_reps))
      self.print_this("Diff steps:", diff_steps)
      self.print_this("Resulting tape:", return_tape.print_with_state(new_state))
      print()
    return True, (
      ProverResult(
        APPLY_RULE,
        new_tape=return_tape,
        num_base_steps=diff_steps,
        states_last_seen=states_last_seen,
      ),
      large_delta,
    )

  # Linear rules can be applied an arbitrary number of times in a single
  # evaluation (like Diff rules), but the expression is slightly more complicated.
  def apply_linear_rule(self, rule, start_config):
    # Unpack input
    start_state, start_tape, start_loop_num = start_config
    current_list = [block.num for block in start_tape.tape[0] + start_tape.tape[1]]
    assert len(current_list) == len(rule.var_list)

    if self.prover_level >= ProverLevel.ITERATED:
      # Don't try to use collatz rules inside meta rules ... we won't know the parity.
      disallow_in_meta_rule = rule.has_collatz_decrease
    else:
      disallow_in_meta_rule = True

    if not _consts_match(rule.var_list, rule.min_list, current_list):
      return False, CONST_MISMATCH
    if not config_fits_min(rule.var_list, rule.min_list, current_list):
      if self.verbose:
        self.print_this("++ Rule cannot apply: Below min")
        print()
      return False, None

    # This rule applies infinitely, we have proven this machine non-halting!
    if rule.infinite:
      if self.verbose:
        self.print_this("++ Rule applies infinitely ++")
        print()
      if rule.states_last_seen:
        states_last_seen = {state: math.inf for state in rule.states_last_seen}
      else:
        states_last_seen = None
      return True, (
        ProverResult(INF_REPEAT, states_last_seen=states_last_seen),
        disallow_in_meta_rule,
      )

    # This rule applies at least once. Find the number of times it applies.
    num_reps = None
    limit_index = None
    limit_final = None
    for i, (cur, func) in enumerate(zip(current_list, rule.func_list)):
      if func and func.is_decreasing:
        if not is_const(cur) and func.has_collatz_decrease:
          if self.verbose:
            self.print_this("++ Collatz diff ++")
          return False, None
        this_reps, this_final = func.max_reps(cur)
        if num_reps is None:
          num_reps = this_reps
          limit_index = i
          limit_final = this_final
        elif is_const(this_reps) and is_const(num_reps):
          if this_reps < num_reps:
            num_reps = this_reps
            limit_index = i
            limit_final = this_final
        else:
          # There are two different decreasing exponents in the rule and at
          # least one is a non-constant expression.
          # We cannot know which one will run out first, so just give up.
          if self.verbose:
            self.print_this("++ Multiple decreasing exponents for expressions ++")
          return False, None

    assert always_ge(num_reps, 0), num_reps
    self.last_rule_var_info = {}
    # Apply rule a finite number of times.
    new_tape = start_tape.copy()
    for i, new_block in enumerate(new_tape.tape[0] + new_tape.tape[1]):
      if rule.var_list[i] is not None and isinstance(new_block.num, Algebraic_Expression):
        in_vars = variables(new_block.num)
        if len(in_vars) == 1:
          in_var = next(iter(in_vars))
          req_min = rule.min_list[i]
          is_lim = i == limit_index
          # WARNING: See apply_diff_rule — assumes no non-limiting decreasing AE blocks.
          self.last_rule_var_info[in_var] = (
            _ae_min_for_var(new_block.num, in_var, delta=-req_min + (0 if is_lim else 1)),
            is_lim,
            req_min,
          )
      if i == limit_index:
        # Directly set the decreasing exponent that reached minimum to avoid
        # subtracting two giant ExpInts.
        new_block.num = limit_final
      elif rule.func_list[i]:
        new_block.num = rule.func_list[i].apply_rep(new_block.num, num_reps)
    for dir in range(2):
      new_tape.tape[dir] = _normalize_half_tape(new_tape.tape[dir])

    if self.verbose:
      self.print_this("++ Iterated rule applied ++")
      self.print_this("Times applied", num_reps)
      self.print_this("Resulting tape:", new_tape)

    # Note: We do not calculate `num_base_steps` and `states_last_seen` (yet).
    return True, (
      ProverResult(APPLY_RULE, new_tape=new_tape),
      disallow_in_meta_rule,
    )


def _subst_var_zero(expr, zero_sub):
  if isinstance(expr, (Algebraic_Expression, Exp_Int.ExpInt)):
    res = Exp_Int.try_simplify(substitute(expr, zero_sub))
    if isinstance(res, Algebraic_Expression):
      new_terms = [ae.Term(term.vars, Exp_Int.try_simplify(term.coef)) for term in res.terms]
      return Algebraic_Expression(new_terms, Exp_Int.try_simplify(res.const))
    return res
  return expr


def _specialize_var_zero(x, initial_tape, gen_sim, min_val):
  """Force variable `x = 0` across in-flight proof state and collapse any zeroed blocks."""
  zero_sub = {x: ConstantToExpression(0)}

  for dir in range(2):
    for block in initial_tape.tape[dir]:
      block.num = _subst_var_zero(block.num, zero_sub)

  for dir in range(2):
    new_half = []
    prefix = gen_sim.min_untouched_prefix[dir] if gen_sim.min_untouched_prefix is not None else None
    for idx, block in enumerate(gen_sim.tape.tape[dir]):
      block.num = _subst_var_zero(block.num, zero_sub)
      if block.num == 0:
        if prefix is not None and idx < prefix:
          prefix = idx
        continue
      if new_half and new_half[-1].symbol == block.symbol:
        new_half[-1].num += block.num
        if prefix is not None:
          prefix = min(prefix, len(new_half) - 1)
      else:
        new_half.append(block)
    gen_sim.tape.tape[dir] = new_half
    if prefix is not None:
      gen_sim.min_untouched_prefix[dir] = min(prefix, len(new_half))

  if isinstance(gen_sim.step_num, Algebraic_Expression):
    gen_sim.step_num = substitute(gen_sim.step_num, zero_sub)
  if gen_sim.states_last_seen:
    for state, last_seen in gen_sim.states_last_seen.items():
      if isinstance(last_seen, Algebraic_Expression):
        gen_sim.states_last_seen[state] = substitute(last_seen, zero_sub)
  min_val.pop(x, None)


def _const_matches(min_val, current_val):
  if getattr(min_val, "is_inf", False):
    return bool(getattr(current_val, "is_inf", False))
  return current_val == min_val


def _ae_min_for_var(expr, x, delta=0):
  """Effective min_val of `x` needed for `expr + delta >= 0`, accounting for linear coefs > 1."""
  c = ae.min_val(expr) + delta
  if len(expr.terms) == 1 and len(expr.terms[0].vars) == 1:
    vp = expr.terms[0].vars[0]
    if vp.var == x and vp.pow == 1 and is_const(expr.terms[0].coef) and expr.terms[0].coef > 1:
      return c // expr.terms[0].coef
  return c


def _nums_equal(n1, n2):
  """Compare two block counts (int, InfNat, Algebraic_Expression, or ExpInt)."""
  if n1 == n2:
    return True
  if getattr(n1, "is_inf", False) or getattr(n2, "is_inf", False):
    return False
  try:
    if always_ge(n1, n2) and always_ge(n2, n1):
      return True
  except (Exp_Int.ExpIntException, TypeError):
    pass
  if isinstance(n1, Algebraic_Expression) and isinstance(n2, Algebraic_Expression):
    if (
      _nums_equal(n1.const, n2.const)
      and len(n1.terms) == len(n2.terms)
      and all(t1.vars == t2.vars and _nums_equal(t1.coef, t2.coef) for t1, t2 in zip(n1.terms, n2.terms))
    ):
      return True
  if isinstance(n1, Exp_Int.ExpInt) and isinstance(n2, Exp_Int.ExpInt):
    if (
      n1.const == n2.const
      and n1.denom == n2.denom
      and len(n1.terms) == len(n2.terms)
      and all(
        t1.base == t2.base and t1.coef == t2.coef and _nums_equal(t1.exponent, t2.exponent)
        for t1, t2 in zip(n1.terms, n2.terms)
      )
    ):
      return True
  # ExpInt represents large towers via a float top; equivalent ASTs can differ slightly.
  if isinstance(n1, Exp_Int.ExpInt):
    try:
      base = n1.terms[0].base
      zero_exp = Exp_Int.ExpInt([Exp_Int.ExpTerm(base, 1, 1)], -base, 1)
      u1 = n1.uparrow_size_approx
      u2 = n2.uparrow_size_approx if isinstance(n2, Exp_Int.ExpInt) else (n2 + zero_exp).uparrow_size_approx
      if u1[0] >= 2 and u1[0] == u2[0] and u1[1] == u2[1] and math.isclose(u1[2], u2[2], rel_tol=1e-6):
        return True
    except (AttributeError, NotImplementedError, Exp_Int.ExpIntException, AssertionError, TypeError):
      pass
  return False


def _tapes_equal(t1, t2):
  """Compare two tapes for --debug-reprove, allowing float tolerance on large ExpInt towers."""
  if t1.dir != t2.dir:
    return False
  for dir in range(2):
    if len(t1.tape[dir]) != len(t2.tape[dir]):
      return False
    for b1, b2 in zip(t1.tape[dir], t2.tape[dir]):
      if b1.symbol != b2.symbol or not _nums_equal(b1.num, b2.num):
        return False
  return True


def _consts_match(var_list, min_list, current_list):
  """Check that all fixed constant blocks (var is None) exactly match `min_list`."""
  return all(
    _const_matches(min_val, current_val)
    for var, min_val, current_val in zip(var_list, min_list, current_list)
    if not var
  )


def config_fits_min(var_list, min_list, current_list, assignment=None):
  """Does `current_list` attain the minimum values (in `min_list`)?
  sets `assignment` along the way."""
  for var, min_val, current_val in zip(var_list, min_list, current_list):
    if var:
      if not always_ge(current_val, min_val):
        return False
      if assignment is not None:
        assignment[var] = current_val
    elif not _const_matches(min_val, current_val):
      return False
  return True


def factor_var(term: Term, k: Variable):
  """Factor out largest power of `k` from `term`."""
  assert isinstance(term, Term), term
  rest_vars = []
  k_pow = 0
  for var_power in term.vars:
    if var_power.var == k:
      k_pow = var_power.pow
    else:
      rest_vars.append(var_power)
  if rest_vars:
    term = Term(var_powers=tuple(rest_vars), coefficient=term.coef)
    return k_pow, Algebraic_Expression(terms=[term], constant=0)
  else:
    # In the common case that there are no other variables, just return an int.
    return k_pow, term.coef


def series_sum(expr: Algebraic_Expression, k: Variable, N):
  """Sums the series expr over k = 0 to N-1 if we can."""
  if isinstance(expr, (int, ConstInt)):
    return int(expr) * N

  assert isinstance(expr, Algebraic_Expression), expr
  assert isinstance(k, Variable), k
  total = expr.const * N
  for term in expr.terms:
    k_pow, rest = factor_var(term, k)
    if k_pow == 0:
      total += rest * N
    elif k_pow == 1:
      # sum_{k=0}^{N-1}(coef * k) = coef * N(N-1)/2
      total += (rest * N * (N - 1)) // 2
    elif k_pow == 2:
      # sum_{k=0}^{N-1}(coef * k^2) = coef * N(N-1)(2N-1)/6
      total += (rest * N * (N - 1) * (2 * N - 1)) // 6
    elif k_pow == 3:
      # sum_{k=0}^{N-1}(coef * k^3) = coef * (N(N-1)/2)^2
      # https://proofwiki.org/wiki/Sum_of_Sequence_of_Cubes
      total += rest * ((N * (N - 1)) // 2) ** 2
    else:
      raise NotImplementedError(f"Cannot series sum {term} over {k}")
  return total
