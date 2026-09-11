#!/usr/bin/env python3
import argparse
from pathlib import Path

import IO
import Halting_Lib
import heapq
import sys

from Macro import Turing_Machine
import TNF

def find_rewinds(tm):
    rev_edges = {s: [] for s in range(tm.num_states)}
    for s in range(tm.num_states):
        trans = tm.trans_table[s][0]
        if trans.condition == Turing_Machine.RUNNING and trans.symbol_out == 0:
            rev_edges[trans.state_out].append(s)
            
    queue = [(0, 0)]
    visited = {0: 0}
    while queue:
        curr, dist = queue.pop(0)
        for prev in rev_edges[curr]:
            if prev not in visited:
                visited[prev] = dist + 1
                queue.append((prev, dist + 1))
                
    rewinds = []
    for s, dist in visited.items():
        if s != 0:
            state_order = list(range(tm.num_states))
            state_order[0], state_order[s] = state_order[s], state_order[0]
            perm_tm = TNF.permute_table(tm, state_order, list(range(tm.num_symbols)))
            tnf_tm = TNF.to_TNF(perm_tm, skip_zeros=False, max_steps=1000)
            if tnf_tm:
                rewinds.append((tnf_tm.ttable_str(), dist))
    return rewinds

def main():
    parser = argparse.ArgumentParser(description="Print the longest running halting TMs.")
    parser.add_argument("infile", type=Path, help="Input protobuf file.")
    parser.add_argument("-n", "--top", type=int, default=20, help="Number of top TMs to print (default: 20)")
    parser.add_argument("--expand-1rb", action="store_true", help="Detect equivalent TMs that start with a 0-writing instruction.")
    args = parser.parse_args()

    # Min-heap to keep track of the top N longest running TMs
    # Elements are tuples: (steps, score, ttable_str)
    halters = []
    
    with IO.Reader(args.infile) as reader:
        try:
            for tm_record in reader:
                status = tm_record.proto.status.halt_status
                if status.is_decided and status.is_halting:
                    steps = Halting_Lib.get_big_int(status.halt_steps)
                    score = Halting_Lib.get_big_int(status.halt_score)
                    item = (steps, score, tm_record.ttable_str())
                    
                    if len(halters) < args.top:
                        heapq.heappush(halters, item)
                    else:
                        heapq.heappushpop(halters, item)
        except IO.Proto.IO_Error as e:
            print(f"WARNING: Stopped reading early due to partial file / unexpected EOF: {e}", file=sys.stderr)
                
    # Sort descending by steps for the final output
    halters.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Top {min(args.top, len(halters))} longest running halting TMs:")
    for i, (steps, score, ttable) in enumerate(halters[:args.top], 1):
        print(f"{i:2d}. {ttable} - steps: {steps:_} - score: {score:_}")
        
        if args.expand_1rb:
            tm = IO.parse_tm(ttable)
            rewinds = find_rewinds(tm)
            for rw, dist in rewinds:
                # The permuted TM takes `dist` extra steps to reach the original state A
                print(f"      {rw} - steps: {steps + dist:_} (rewind {dist})")

if __name__ == "__main__":
    main()
