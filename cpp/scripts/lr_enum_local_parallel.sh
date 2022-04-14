#!/bin/bash

set -u
set -e

if [ $# -ne 5 ]; then
  echo "Usage: $0 states symbols init_steps max_steps num_procs" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
INIT_STEPS=$3
MAX_STEPS=$4
NUM_PROCESSES=$5

DATA_DIR="./data/lin_recur/${NUM_STATES}x${NUM_SYMBOLS}/${MAX_STEPS}/${NUM_PROCESSES}/"

rm -rf $DATA_DIR
mkdir -p $DATA_DIR

echo
date
echo "(1) Enumerating a small number of steps to get a bunch of machines."
./lr_enum $NUM_STATES $NUM_SYMBOLS $INIT_STEPS ${DATA_DIR}/inf_init.txt ${DATA_DIR}/unknown_init.txt

echo
date
echo "(2) Splitting those machines into chunks."
python3 scripts/shuffle_split.py ${DATA_DIR}/unknown_init.txt $NUM_PROCESSES

echo
date
echo "(3) Continue enumeration on each chunk as a separate process in parallel."
for chunk_num in $(seq 0 $((NUM_PROCESSES - 1))); do
  INPUT_TMS=${DATA_DIR}/unknown_init.txt.part_${chunk_num}_of_${NUM_PROCESSES}
  ./lr_enum_continue $INPUT_TMS $MAX_STEPS ${DATA_DIR}/inf_part_${chunk_num}_of_${NUM_PROCESSES} ${DATA_DIR}/unknown_part_${chunk_num}_of_${NUM_PROCESSES} ${chunk_num} &
done
echo "Waiting for all the enumerations to complete."
wait

echo
date
echo "(4) Merging the results and compute the LB."
cat ${DATA_DIR}/inf_init.txt ${DATA_DIR}/inf_part_*_of_${NUM_PROCESSES} > ${DATA_DIR}/inf_final.txt
cat ${DATA_DIR}/unknown_part_*_of_${NUM_PROCESSES} > ${DATA_DIR}/unknown_final.txt

echo
date
echo "Finished"
