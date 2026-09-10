#!/usr/bin/env python3
import argparse
from pathlib import Path

from Enumerate import enumerate
from Pipeline import Pipeline, SimulatorDecider, RevEngDecider, LinRecurDecider

def main():
    parser = argparse.ArgumentParser(description="Run BB(2,2) pipeline.")
    parser.add_argument("outfile", type=Path, help="Output protobuf file.")
    args = parser.parse_args()

    pipeline = Pipeline([
        RevEngDecider(),
        SimulatorDecider(10),
        LinRecurDecider(10),
    ])

    enumerate(2, 2, pipeline, args.outfile)

if __name__ == "__main__":
    main()
