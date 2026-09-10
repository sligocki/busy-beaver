#!/usr/bin/env python3
import argparse
from pathlib import Path

import IO
import Halting_Lib

import heapq

def main():
    parser = argparse.ArgumentParser(description="Print the longest running halting TMs.")
    parser.add_argument("infile", type=Path, help="Input protobuf file.")
    parser.add_argument("-n", "--top", type=int, default=20, help="Number of top TMs to print (default: 20)")
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
            import sys
            print(f"WARNING: Stopped reading early due to partial file / unexpected EOF: {e}", file=sys.stderr)
                
    # Sort descending by steps for the final output
    halters.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Top {min(args.top, len(halters))} longest running halting TMs:")
    for i, (steps, score, ttable) in enumerate(halters[:args.top], 1):
        print(f"{i:2d}. {ttable} - steps: {steps:_} - score: {score:_}")

if __name__ == "__main__":
    main()
