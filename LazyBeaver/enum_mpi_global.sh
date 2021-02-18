#!/bin/bash

set -u
set -e

if [ $# -ne 7 ]; then
  echo "Usage: $0 states symbols init_steps max_steps procs_per_node num_nodes base_name" 1>&2
  exit 1
fi

NUM_STATES=$1
NUM_SYMBOLS=$2
INIT_STEPS=$3
MAX_STEPS=$4
PROCS_PER_NODE=$5
NUM_NODES=$6
BASE_NAME=$7

TOP_DATA_DIR="${BASE_NAME}/${NUM_STATES}x${NUM_SYMBOLS}/${INIT_STEPS}/"

if [ -d $TOP_DATA_DIR ]; then
  echo "Directory '"${TOP_DATA_DIR}"' exists - exiting..."
  exit 1
fi

mkdir -p $TOP_DATA_DIR

echo
date
echo "(1) Enumerating a small number of steps to get a bunch of machines."
./lazy_beaver_enum $NUM_STATES $NUM_SYMBOLS $INIT_STEPS ${TOP_DATA_DIR}/steps_init ${TOP_DATA_DIR}/tms_init

echo
date
echo "(2) Splitting those machines into chunks for each node."
./shuffle_split.py ${TOP_DATA_DIR}/tms_init ${NUM_NODES}

echo
date
echo "(3) Continue enumeration on each chunk on individual nodes."
srun -n $NUM_NODES -N $NUM_NODES ./enum_mpi_local.sh $NUM_STATES $NUM_SYMBOLS $INIT_STEPS $MAX_STEPS $PROCS_PER_NODE $NUM_NODES $TOP_DATA_DIR
echo "Waiting for all the enumerations to complete."
wait

echo
date
echo "(4) Merging the results and compute the LB."
./merge_steps_examples.py ${TOP_DATA_DIR}/node.*/steps_final > ${TOP_DATA_DIR}/steps_final

echo
date
echo "(5) Finished"
