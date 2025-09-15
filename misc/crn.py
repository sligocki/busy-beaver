# Exploration of BB for surface CRNs: 
#
# Clamons S, Qian L, Winfree E. 2020 Programming and simulating chemical
#   reaction networks on a surface. J. R. Soc. Interface 17: 20190790.
#   http://dx.doi.org/10.1098/rsif.2019.0790

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import itertools
import math
import time
from typing import Iterator


type SpeciesID = int
type SpeciesPair = tuple[SpeciesID, SpeciesID]
type ReactionMap = dict[SpeciesPair, list[SpeciesPair]]

BLANK_SPECIES: SpeciesID = 0
SEED_SPECIES: SpeciesID = 1

@dataclass(frozen=True)
class Reaction22:
  in1: SpeciesID
  in2: SpeciesID
  out1: SpeciesID
  out2: SpeciesID

  def __str__(self) -> str:
    return f"{self.in1} + {self.in2} -> {self.out1} + {self.out2}"
  
  def max(self) -> SpeciesID:
    return max(self.in1, self.in2, self.out1, self.out2)

@dataclass(frozen=True)
class CRN:
  reactions: list[Reaction22]

  def num_species(self) -> int:
    if not self.reactions:
      return 0
    return max(r.max() for r in self.reactions) + 1

  def __str__(self) -> str:
    return f"CRN({len(self.reactions)},{self.num_species()}):\n  " + "\n  ".join(str(r) for r in self.reactions)
  
  def reaction_map(self) -> ReactionMap:
    ret = defaultdict(list)
    for r in self.reactions:
      ret[(r.in1, r.in2)].append((r.out1, r.out2))
      ret[(r.in2, r.in1)].append((r.out2, r.out1))
    return dict(ret)

@dataclass(frozen=True)
class Config:
  """Linear (1D) lattice configuration. Represented by a finite list of species in order."""
  data: tuple[SpeciesID, ...]

  def enum_children(self, rxn_map: ReactionMap) -> Iterator[Config]:
    padded_data = (BLANK_SPECIES,) + self.data + (BLANK_SPECIES,)
    for i, (a, b) in enumerate(itertools.pairwise(padded_data)):
      # print(i, a, b, rxn_map.get((a, b)), rxn_map)
      for (c, d) in rxn_map.get((a, b), []):
        yield self.update(i, c, d)

  def update(self, index: int, c: SpeciesID, d: SpeciesID) -> Config:
    start = max(index-1, 0)
    end = index+1
    new_data = list(self.data)
    new_data[start:end] = [c, d]
    return Config(tuple(new_data))
  
  def sigma_score(self) -> int:
    """Number of non-zero symbols left on tape."""
    # NOTE: This is technically not the same as the score function from Clamons (which counts only one species).
    return sum(1 for x in self.data if x != BLANK_SPECIES)


def score_crn(crn: CRN, max_configs = math.inf) -> int:
  """Simulate all possible trajectories of CRN and return it's Busy Beaver score (if it qualifies)."""
  rxn_map = crn.reaction_map()
  seed_config = Config((SEED_SPECIES,))
  todo = [seed_config]
  seen = {seed_config}
  score = 0
  num_terminal = 0
  while todo:
    if len(seen) >= max_configs:
      # Gave up searching
      return 0
    config = todo.pop()
    is_terminal = True
    for new_config in config.enum_children(rxn_map):
      # print(config, new_config)
      is_terminal = False
      if new_config not in seen:
        todo.append(new_config)
        seen.add(new_config)
    if is_terminal:
      num_terminal += 1
      this_score = config.sigma_score()
      if not score:
        score = this_score
      elif score != this_score:
        # This CRN has inconsistent scores based on different trajectories, it is not a BB candidate.
        return 0
  # All trajectories have same score (or no trajectories terminated -> 0)
  # Note: This is not 100% accurate. We should also check that all configs can reach a terminal config (there are no terminal cycles).
  return score, len(seen), num_terminal


# Generators for CRNs
def bloom(n: int) -> CRN:
  """The 2^n bloom from Clamons paper."""
  # k + _ -> (k+1) + (k+1)
  splits = [Reaction22(k, 0, k+1, k+1) for k in range(1, n+1)]
  # F = n+1
  # k + F -> F + k
  diffusion = [Reaction22(k, n+1, n+1, k) for k in range(2, n+1)]
  return CRN(tuple(splits + diffusion))

def tm_crn(tm_str: str) -> CRN:
  """Convert TM into CRN."""
  ttable = [list(itertools.batched(row, 3)) for row in tm_str.split("_")]
  num_states = len(ttable)
  num_symbols = len(ttable[0])
  # states_used = {trans[1:] for row in ttable for trans in row}
  # symbols_used = {trans[:2] for row in ttable for trans in row}

  def dir2int(dir: str):
    if dir == "R": return 0
    else: return 1
  def s2sp(state: int, dir: str): return 2*state + dir2int(dir) + 1
  def q2sp(symb: int, dir: str): return 2*symb + 2*num_states + dir2int(dir) + 1

  rxns = []
  for s_in, row in enumerate(ttable):
    for q_in, trans in enumerate(row):
      if trans[2] not in ("-", "Z"):
        q_out = int(trans[0])
        dir = trans[1]
        s_out = "ABCDEFG".index(trans[2])
        if dir == "R":
          # s_in> + q_in R -> q_out L + s_out>
          rxns.append(Reaction22(
            s2sp(s_in, "R"), q2sp(q_in, "R"),
            q2sp(q_out, "L"), s2sp(s_out, "R")))
          # q_in L + <s_in -> q_out L + s_out>
          rxns.append(Reaction22(
            q2sp(q_in, "L"), s2sp(s_in, "L"),
            q2sp(q_out, "L"), s2sp(s_out, "R")))
          if q_in == 0:
            rxns.append(Reaction22(
              s2sp(s_in, "R"), BLANK_SPECIES,
              q2sp(q_out, "L"), s2sp(s_out, "R")))
            rxns.append(Reaction22(
              BLANK_SPECIES, s2sp(s_in, "L"),
              q2sp(q_out, "L"), s2sp(s_out, "R")))
        else:
          # s_in> + q_in R -> <s_out + q_out R
          rxns.append(Reaction22(
            s2sp(s_in, "R"), q2sp(q_in, "R"),
            s2sp(s_out, "L"), q2sp(q_out, "R")))
          # q_in L + <s_in -> <s_out + q_out R
          rxns.append(Reaction22(
            q2sp(q_in, "L"), s2sp(s_in, "L"),
            s2sp(s_out, "L"), q2sp(q_out, "R")))
          if q_in == 0:
            rxns.append(Reaction22(
              s2sp(s_in, "R"), BLANK_SPECIES,
              s2sp(s_out, "L"), q2sp(q_out, "R")))
            rxns.append(Reaction22(
              BLANK_SPECIES, s2sp(s_in, "L"),
              s2sp(s_out, "L"), q2sp(q_out, "R")))
  return CRN(rxns)

for n in range(5):
  crn = bloom(n)
  score = score_crn(crn)
  print(f"Bloom({n}) = {score}\t({time.process_time():.2f}s)")

bb4 = tm_crn("1RB1LB_1LA0LC_---1LD_1RD0RA")
score = score_crn(bb4)
print(f"BB4 = {score}\t({time.process_time():.2f}s)")

bb5 = tm_crn("1RB1LC_1RC1RB_1RD0LE_1LA1LD_---0LA")
score = score_crn(bb5)
print(f"BB5 = {score}\t({time.process_time():.2f}s)")
