import argparse
import math
from collections import defaultdict


def parse_tm(tm_str):
  states = tm_str.split("_")
  transitions = {}
  for i, state_str in enumerate(states):
    state_name = chr(ord("A") + i)
    transitions[state_name] = {}
    # Assuming 3 chars per symbol transition
    num_symbols = len(state_str) // 3
    for symbol in range(num_symbols):
      trans = state_str[symbol * 3 : (symbol + 1) * 3]
      if trans == "---":
        transitions[state_name][symbol] = None
      else:
        write_sym = int(trans[0])
        dir_char = trans[1]
        next_state = trans[2]
        transitions[state_name][symbol] = (write_sym, dir_char, next_state)
  return transitions


def main():
  parser = argparse.ArgumentParser(description="Simulate TM and track beeps/boops")
  parser.add_argument("tm_str", help="TM string, e.g. 0RB0LC_1LC1RB_0RB1LA")
  parser.add_argument("beep_transitions", help="Comma-separated beep transitions, e.g. A1,C0")
  parser.add_argument("boop_transitions", help="Comma-separated boop transitions, e.g. A0,B0,B1,C1")
  parser.add_argument("num_steps", type=int, nargs="?", default=math.inf)
  parser.add_argument("-s", "--summary", action="store_true", help="Quiet intermediate printing, only show summary")
  args = parser.parse_args()

  tm_str = args.tm_str
  beep_strs = set(args.beep_transitions.split(",")) if args.beep_transitions else set()
  boop_strs = set(args.boop_transitions.split(",")) if args.boop_transitions else set()
  summary = args.summary

  transitions = parse_tm(tm_str)

  tape = defaultdict(int)
  head = 0
  state = "A"
  step = 1
  beeps = 0

  # Track beep_count -> {'first': step, 'last': step}
  beep_count_stats = {}

  try:
    while step < args.num_steps:
      symbol = tape[head]
      trans_name = f"{state}{symbol}"

      if trans_name in beep_strs:
        beeps += 1

      if trans_name in boop_strs:
        if not summary:
          print(f"{beeps} beeps, boop {trans_name}, step {step}")

        if beeps not in beep_count_stats:
          beep_count_stats[beeps] = {"first": step, "last": step}
        else:
          beep_count_stats[beeps]["last"] = step

        beeps = 0

      trans = transitions.get(state, {}).get(symbol)
      if trans is None:
        if not summary:
          print(f"Halted at step {step} (undefined transition)")
        break

      write_sym, dir_char, next_state = trans
      tape[head] = write_sym

      if dir_char == "R":
        head += 1
      elif dir_char == "L":
        head -= 1

      state = next_state

      if state == "H" or state == "Z":
        if not summary:
          print(f"Halted at step {step}")
        break

      step += 1
  except KeyboardInterrupt:
    if not summary:
      print("\nInterrupted by user.")
  finally:
    print("\n--- Summary ---")
    if not beep_count_stats:
      print("No boops occurred.")
    else:
      print(f"{'Beep Count':<12} | {'First Step':<15} | {'Last Step':<15}")
      print("-" * 48)
      for count in sorted(beep_count_stats.keys()):
        stats = beep_count_stats[count]
        print(f"{count:<12} | {stats['first']:<15} | {stats['last']:<15}")


if __name__ == "__main__":
  try:
    main()
  except BrokenPipeError:
    pass
