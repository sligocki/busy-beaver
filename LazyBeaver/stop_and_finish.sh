#!/bin/bash

set -u
set -e

if [ $# -ne 6 ]; then
  echo "Usage: $0 states symbols init_steps max_steps num_procs index" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
INIT_STEPS=$3
MAX_STEPS=$4
NUM_PROCESSES=$5
INDEX=$6

OUT_FILE="${NUM_STATES}.${NUM_SYMBOLS}.${NUM_PROCESSES}.out"
SAVE_FILE="${NUM_STATES}.${NUM_SYMBOLS}.${NUM_PROCESSES}.${MAX_STEPS}.out.${INDEX}"

DATA_DIR="./data/${NUM_STATES}x${NUM_SYMBOLS}/${INIT_STEPS}/"
SAVE_DIR="./data.${NUM_STATES}.${NUM_SYMBOLS}.${MAX_STEPS}.${INDEX}"

make

echo
date
echo "(1) Stopping run."
/bin/touch stop.enumeration
/bin/sleep 60
/bin/rm stop.enumeration

echo
date
echo "(2) Saving data."
/bin/mv ${OUT_FILE} ${SAVE_FILE}
/bin/mv data ${SAVE_DIR}

echo
date
echo "Finished"
