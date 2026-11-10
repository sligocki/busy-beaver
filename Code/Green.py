"""Generator for Green's Turing Machines.

Based on Milton W. Green (1964), "A Lower Bound on Rado's Sigma Function for Binary Turing Machines",
and Shawn Ligocki's description:
https://www.sligocki.com/2023/10/19/greens-machines.html

The machines consist of:
1. A setup component:
   - 3-state setup S_3 for even states (BB_{2k+4}, n >= 6)
   - 4-state setup S_4 for odd states (BB_{2k+5}, n >= 7)
2. A compute component G_m (m = 2k+1):
   - States Q_m, T_m, Q_{m-2}, T_{m-2}, ..., Q_3, T_3, Q_1
   - Exit state is A for S_3 and C for S_4.
"""

import argparse

import IO
from Macro import Turing_Machine


def green_machine_str(num_states: int) -> str:
  """Produce the standard 1-line text representation of an n-state Green machine.

  Matches files like Machines/10x2-Green.
  """
  if num_states < 6:
    raise ValueError(f"Green machines are defined for num_states >= 6, got {num_states}")

  halt_str = Turing_Machine.halt_state_str(num_states)

  if num_states % 2 == 0:
    # 3-state setup S_3
    # A (exit): 0 -> 1 L B, 1 -> 1 R Z
    # B:        0 -> 0 L C, 1 -> 1 L C
    # C (T):    0 -> 0 L Q_n (D), 1 -> 0 L T (C)
    start_state = 3
    exit_state = 0  # A
    transitions = [
      [f"1L{Turing_Machine.state_to_str(1)}", f"1R{halt_str}"],
      [f"0L{Turing_Machine.state_to_str(2)}", f"1L{Turing_Machine.state_to_str(2)}"],
      [f"0L{Turing_Machine.state_to_str(3)}", f"0L{Turing_Machine.state_to_str(2)}"],
    ]
  else:
    # 4-state setup S_4
    # A:        0 -> 1 L T (D), 1 -> 1 L B
    # B:        0 -> 1 L Z, 1 -> 1 L A
    # C (exit): 0 -> 0 L B, 1 -> 1 L T (D)
    # D (T):    0 -> 0 L Q_n (E), 1 -> 0 L T (D)
    start_state = 4
    exit_state = 2  # C
    transitions = [
      [f"1L{Turing_Machine.state_to_str(3)}", f"1L{Turing_Machine.state_to_str(1)}"],
      [f"1L{halt_str}", f"1L{Turing_Machine.state_to_str(0)}"],
      [f"0L{Turing_Machine.state_to_str(1)}", f"1L{Turing_Machine.state_to_str(3)}"],
      [f"0L{Turing_Machine.state_to_str(4)}", f"0L{Turing_Machine.state_to_str(3)}"],
    ]

  # Compute component G_m where m = num_states - start_state = 2k + 1
  m = num_states - start_state
  k = (m - 1) // 2

  for j in range(m):
    state_idx = start_state + j
    if j == 2 * k:
      # State Q_1:
      # 0 -> 1 R Q_1 (self-loop)
      # 1 -> 1 R Q_3 (start_state + j - 2)
      t0 = f"1R{Turing_Machine.state_to_str(state_idx)}"
      t1 = f"1R{Turing_Machine.state_to_str(start_state + j - 2)}"
    elif j % 2 == 1:
      # State T_r:
      # 0 -> 0 L Q_{r-2} (state_idx + 1)
      # 1 -> 0 L T_r (self-loop)
      t0 = f"0L{Turing_Machine.state_to_str(state_idx + 1)}"
      t1 = f"0L{Turing_Machine.state_to_str(state_idx)}"
    else:
      # State Q_r (r >= 3):
      # 0 -> 1 L T_r (state_idx + 1)
      # 1 -> 1 R Q_{r+2} (for r=m: exit_state; for r < m: start_state + j - 2)
      t0 = f"1L{Turing_Machine.state_to_str(state_idx + 1)}"
      if j == 0:
        t1 = f"1R{Turing_Machine.state_to_str(exit_state)}"
      else:
        t1 = f"1R{Turing_Machine.state_to_str(start_state + j - 2)}"
    transitions.append([t0, t1])

  return "_".join("".join(t) for t in transitions)


def green_machine(num_states: int) -> Turing_Machine.Simple_Machine:
  """Produce an n-state Green Turing machine as a Simple_Machine object."""
  return IO.parse_tm(green_machine_str(num_states))


green_tm = green_machine


def main():
  parser = argparse.ArgumentParser(description="Generate Green Turing machines.")
  parser.add_argument("states", type=int, help="Number of states (>= 6)")
  args = parser.parse_args()

  print(green_machine_str(args.states))


if __name__ == "__main__":
  main()
