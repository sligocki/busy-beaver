#!/bin/bash

set -u
set -e

if [ $# -lt 6 ] || [ $# -gt 8 ]; then
  echo "Usage: $0 states symbols allow_no_halt init_steps max_steps num_procs [compress_output [only_unknown]]" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
ALLOW_NO_HALT=$3
INIT_STEPS=$4
MAX_STEPS=$5
NUM_PROCESSES=$6

if [ $# -ge 7 ]; then
  COMPRESS_OUTPUT=$7
else
  COMPRESS_OUTPUT="false"
fi

if [ $# -eq 8 ]; then
  ONLY_UNKNOWN=$8
else
  ONLY_UNKNOWN="false"
fi

echo $COMPRESS_OUTPUT $ONLY_UNKNOWN

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
  ${ALLOW_NO_HALT} \
  false \
  ${ONLY_UNKNOWN}

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
    ${chunk_num} \
    ${ALLOW_NO_HALT} \
    ${COMPRESS_OUTPUT} \
    ${ONLY_UNKNOWN} &
done
echo "Waiting for all the enumerations to complete."
wait

if [ "${COMPRESS_OUTPUT}" = "true" ]; then
  gzip ${DATA_DIR}/*_init*txt*
fi

echo
date
echo "(4) Merging the results"
if [ "${COMPRESS_OUTPUT}" = "false" ]; then
  cat ${DATA_DIR}/halt_init.txt* ${DATA_DIR}/halt_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/halt_final.txt
  cat ${DATA_DIR}/inf_init.txt* ${DATA_DIR}/inf_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/inf_final.txt
  # Note: We don't include ${DATA_DIR}/unknown_init.txt which is redundant.
  cat ${DATA_DIR}/unknown_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/unknown_final.txt
else
  cat ${DATA_DIR}/halt_init.txt* ${DATA_DIR}/halt_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/halt_final.txt.gz
  cat ${DATA_DIR}/inf_init.txt* ${DATA_DIR}/inf_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/inf_final.txt.gz
  # Note: We don't include ${DATA_DIR}/unknown_init.txt which is redundant.
  cat ${DATA_DIR}/unknown_part_*_of_${NUM_PROCESSES}* > ${DATA_DIR}/unknown_final.txt.gz
fi

echo
date
echo "Finished"
