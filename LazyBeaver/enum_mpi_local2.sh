#!/bin/bash

set -u
set -e

if [ $# -ne 7 ]; then
  echo "Usage: $0 states symbols init_steps max_steps num_procs num_nodes base_name" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
INIT_STEPS=$3
MAX_STEPS=$4
NUM_PROCESSES=$5
NUM_NODES=$6
BASE_NAME=$7

MPI_PROC=${SLURM_PROCID}
MPI_PROC_ZEROS=`echo ${MPI_PROC} | awk '{printf("%04d",$1);}'`

INIT_DATA="${BASE_NAME}/tms_init.part_${MPI_PROC}_of_${NUM_NODES}"
DATA_DIR="${BASE_NAME}/node.${MPI_PROC_ZEROS}"

if [ -d $DATA_DIR ]; then
  echo "Directory '"${DATA_DIR}"' exists - exiting..."
  exit 1
fi

mkdir -p $DATA_DIR

mv ${INIT_DATA} ${DATA_DIR}/tms_init

while [ -s ${DATA_DIR}/tms_init ]
do
  echo
  date
  echo "(${MPI_PROC}:1) Splitting machines into chunks."
  ./shuffle_split.py ${DATA_DIR}/tms_init $NUM_PROCESSES

  echo
  date
  echo "(${MPI_PROC}:2) Continue enumeration on each chunk as a separate process in parallel."
  for chunk_num in $(seq 0 $((NUM_PROCESSES - 1))); do
    INPUT_TMS=${DATA_DIR}/tms_init.part_${chunk_num}_of_${NUM_PROCESSES}
    ./continue_enum $INPUT_TMS $MAX_STEPS ${DATA_DIR}/steps_part_${chunk_num}_of_${NUM_PROCESSES} ${DATA_DIR}/stack_part_${chunk_num}_of_${NUM_PROCESSES} ${chunk_num} ${DATA_DIR}/stop.enumeration &
  done

  echo "${MPI_PROC}:3) Waiting."
  sleep 60

  echo "${MPI_PROC}:4) Halting processes."
  touch "${DATA_DIR}/stop.enumeration"
  sleep 5
  /bin/rm "${DATA_DIR}/stop.enumeration"

  echo "${MPI_PROC}:5) Rebalancing queues."
  cat ${DATA_DIR}/stack_* > ${DATA_DIR}/tms_init
  /bin/rm ${DATA_DIR}/stack_*

  echo
  date
  echo "(${MPI_PROC}:6) Merging the results."
  ./merge_steps_examples.py ${DATA_DIR}/steps_* > ${DATA_DIR}/temp_steps
  /bin/mv ${DATA_DIR}/temp_steps ${DATA_DIR}/steps_final
done

echo
date
echo "(${MPI_PROC}:7) Finished"
