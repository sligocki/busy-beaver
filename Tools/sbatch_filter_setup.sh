#!/bin/bash
#SBATCH -J bb_setup
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH -t 2:00:00
#SBATCH -o bb_setup-%J.txt
#
# Simple, serial, startup job to prepare data for sbatch_filter_array.sh to run
# in parallel.

set -e
set -u
set -x

ROOT_DIR=$1
SUBDIR=$2
NUM_SHARDS=$3

WORK_DIR=${ROOT_DIR}/${SUBDIR}/
rm -rf ${WORK_DIR}
mkdir -p ${WORK_DIR}/split/in/ ${WORK_DIR}/logs/

# Pull in holdouts from previous filter (skip this copy if holdouts file is too large).
if [[ "$(wc -c < ${ROOT_DIR}/unknown.txt)" < 10000000000 ]]; then
  cp ${ROOT_DIR}/unknown.txt ${WORK_DIR}/in.txt
fi

# Split inputs into shards so that array job can run.
split --number=l/${NUM_SHARDS} --numeric-suffixes --suffix-length=8 \
  ${ROOT_DIR}/unknown.txt ${WORK_DIR}/split/in/in.
