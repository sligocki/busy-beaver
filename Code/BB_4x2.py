#!/usr/bin/env python3
import argparse
from pathlib import Path

from Enumerate import enumerate
from Pipeline import Pipeline, SimulatorDecider, RevEngDecider, LinRecurDecider, CTLDecider, CpsDecider

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("outfile", type=Path, help="Output protobuf file.")
    args = parser.parse_args()

    pipeline = Pipeline([
        RevEngDecider(),
        LinRecurDecider(100),
        SimulatorDecider(1000),
        CpsDecider(max_block_size=6),
        CTLDecider(type="CTL2", max_block_size=6),
        CTLDecider(type="CTL1", max_block_size=6),
        CTLDecider(type="CTL3", max_block_size=6),
        CTLDecider(type="CTL4", max_block_size=6),
        SimulatorDecider(10000),
        CpsDecider(max_block_size=6, fixed_history=1),
    ])

    enumerate(4, 2, pipeline, args.outfile)

if __name__ == "__main__":
    main()
