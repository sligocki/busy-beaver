#!/bin/bash
#SBATCH -J bb_init
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -t 1:00:00
#SBATCH -o enum_init-%j.txt

set -e
set -u
set -x

WORK_DIR=$1
shift
NUM_CHUNKS=$1
shift

BASENAME=${WORK_DIR}/init
mkdir -p ${WORK_DIR}

# Enumerate a handful of machines.
time python3 Code/Enumerate.py \
  --allow-no-halt --no-reverse-engineer --no-ctl \
  --breadth-first --num-enum=10000 \
  --force --time=0 \
  --outfile=${BASENAME}.out \
  "$@"

time python2 Tools/Integrate_Data.py ${BASENAME}

time split --number="r/${NUM_CHUNKS}" --numeric-suffixes --suffix-length=8 \
  ${BASENAME}.unknown \
  ${BASENAME}.split.unknown.

echo Success
