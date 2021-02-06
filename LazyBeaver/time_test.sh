#!/bin/bash

set -u
set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 max_steps num_procs" 1>&2
  exit 1
fi

MAX_STEPS=$1
NUM_PROCESSES=$2

echo
date
echo "(3) Continue enumeration on each chunk as a separate process in parallel."
for chunk_num in $(seq 0 $((NUM_PROCESSES - 1))); do
  ./time_test $MAX_STEPS > /dev/null &
done
echo "Waiting for all the enumerations to complete."
wait
date
