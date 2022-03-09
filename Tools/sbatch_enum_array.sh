#!/bin/bash
#SBATCH -J bb
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -a 0-999%100
#SBATCH -t 4:00:00
#SBATCH -o enum-%A_%a.txt

set -e
set -u
set -x

WORK_DIR=$1
shift

INDEX=$(printf "%08d" $SLURM_ARRAY_TASK_ID)

time python3 Code/Enumerate.py \
  --allow-no-halt --no-reverse-engineer --no-ctl \
  --force --time=0 \
  --infile=${WORK_DIR}/init.split.unknown.${INDEX} \
  --outfile=${WORK_DIR}/array_${INDEX}.out \
  "$@"

echo Success
