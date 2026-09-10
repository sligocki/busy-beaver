#!/usr/bin/env python3
import argparse
from pathlib import Path

from Enumerate import enumerate
from Pipeline import Pipeline, SimulatorDecider, RevEngDecider, LinRecurDecider, CTLDecider

def main():
    parser = argparse.ArgumentParser(description="Run BB(2,2) pipeline.")
    parser.add_argument("outfile", type=Path, help="Output protobuf file.")
    args = parser.parse_args()

    pipeline = Pipeline([
        RevEngDecider(),
        SimulatorDecider(),
        LinRecurDecider(127),
        CTLDecider(type="CTL2", max_block_size=6),
    ])

    enumerate(3, 2, pipeline, args.outfile)

if __name__ == "__main__":
    main()
