#!/usr/bin/env python3
import argparse
from pathlib import Path

from Enumerate import enumerate
from Pipeline import (
  CpsDecider,
  LinRecurDecider,
  Pipeline,
  RevEngDecider,
  SimulatorDecider,
)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("outfile", type=Path, help="Output protobuf file.")
  args = parser.parse_args()

  pipeline = Pipeline(
    [
      RevEngDecider(),
      SimulatorDecider(100),
      LinRecurDecider(100),
      CpsDecider(max_block_size=3),
      SimulatorDecider(10000),
    ]
  )

  enumerate(2, 3, pipeline, args.outfile)


if __name__ == "__main__":
  main()
