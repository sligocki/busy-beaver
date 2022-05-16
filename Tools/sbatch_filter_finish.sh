#!/bin/bash
#SBATCH -J bb_finish
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH -o bb_finish-%J.txt
#
# Simple, serial job to combine the results of all sbatch_filter_array.sh jobs
# and prepare us to run the next filter.

set -e
set -u
set -x

ROOT_DIR=$1
SUBDIR=$2
NUM_SHARDS=$3

WORK_DIR=${ROOT_DIR}/${SUBDIR}/
TMP_DIR=/tmp/${USER}-$$/
rm -rf ${TMP_DIR}
mkdip -p ${TMP_DIR}

# Make sure all shards succeeded.
if (( $(ls ${WORK_DIR}/split/0*/success | wc -l) != ${NUM_SHARDS})); then
  exit 1
fi

# Combine outputs
for x in halt.{small,large}.pb qhalt.{small,large}.pb infinite.pb unknown.pb; do
  cat ${WORK_DIR}/split/0*/${x} > ${WORK_DIR}/${x}
done

# Update holdouts for next filter
cat ${WORK_DIR}/split/0*/unknown.txt > ${ROOT_DIR}/unknown.txt

# TODO: Update to Halt (and QHalt) machines
# TODO: Read stats (runtime, # Categorized in each way)
# TODO: Print summary of stats
# TODO: Write stats to CSV (to replace my spreadsheet)
