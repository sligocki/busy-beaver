#!/bin/bash

set -u
set -e

if [ $# -ne 6 ]; then
  echo "Usage: $0 states symbols allow_no_halt init_steps max_steps num_procs" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
ALLOW_NO_HALT=$3
INIT_STEPS=$4
MAX_STEPS=$5
NUM_PROCESSES=$6

DATA_DIR="./data/lin_recur/${NUM_STATES}x${NUM_SYMBOLS}/${MAX_STEPS}/${NUM_PROCESSES}/"

rm -rf $DATA_DIR
mkdir -p $DATA_DIR

echo
date
echo "(1) Enumerating a small number of steps to get a bunch of machines."
./lr_enum \
  $NUM_STATES $NUM_SYMBOLS $INIT_STEPS \
  ${DATA_DIR}/halt_init.txt \
  ${DATA_DIR}/inf_init.txt \
  ${DATA_DIR}/unknown_init.txt \
  ${ALLOW_NO_HALT}

echo
date
echo "(2) Splitting those machines into chunks."
python3 scripts/shuffle_split.py ${DATA_DIR}/unknown_init.txt $NUM_PROCESSES

echo
date
echo "(3) Continue enumeration on each chunk as a separate process in parallel."
for chunk_num in $(seq 0 $((NUM_PROCESSES - 1))); do
  ./lr_enum_continue \
    ${DATA_DIR}/unknown_init.txt.part_${chunk_num}_of_${NUM_PROCESSES} \
    $MAX_STEPS \
    ${DATA_DIR}/halt_part_${chunk_num}_of_${NUM_PROCESSES} \
    ${DATA_DIR}/inf_part_${chunk_num}_of_${NUM_PROCESSES} \
    ${DATA_DIR}/unknown_part_${chunk_num}_of_${NUM_PROCESSES} \
    ${chunk_num} ${ALLOW_NO_HALT} &
done
echo "Waiting for all the enumerations to complete."
wait

echo
date
echo "(4) Merging the results"
cat ${DATA_DIR}/halt_init.txt ${DATA_DIR}/halt_part_*_of_${NUM_PROCESSES} > ${DATA_DIR}/halt_final.txt
cat ${DATA_DIR}/inf_init.txt ${DATA_DIR}/inf_part_*_of_${NUM_PROCESSES} > ${DATA_DIR}/inf_final.txt
# Note: We don't include ${DATA_DIR}/unknown_init.txt which is redundant.
cat ${DATA_DIR}/unknown_part_*_of_${NUM_PROCESSES} > ${DATA_DIR}/unknown_final.txt

echo
date
echo "Finished"
