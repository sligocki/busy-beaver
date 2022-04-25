#!/bin/bash
#SBATCH -J bb
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1
#SBATCH -o enum-%A_%a.txt

set -e
set -u
set -x

WORK_DIR=$1
shift

INDEX=$(printf "%08d" $SLURM_ARRAY_TASK_ID)
OUT_DIR=${WORK_DIR}/${INDEX}/
IN_FILE=${WORK_DIR}/in/in.${INDEX}

rm -rf ${OUT_DIR}
mkdir -p ${OUT_DIR}


# Do enumeration
time python3 Code/Enumerate.py \
  --infile=${IN_FILE} \
  --outfile=${OUT_DIR}/out.pb --outformat=protobuf --force \
  "$@"

# Check that we didn't lose any TMs
NUM_BEFORE=$(python3 Code/Count.py ${IN_FILE})
NUM_AFTER=$(python3 Code/Count.py ${OUT_DIR}/out.pb)

if (( $NUM_BEFORE != $NUM_AFTER )); then
  echo "Failure: Number of machines changed: $NUM_BEFORE != $NUM_AFTER"
  exit 1
fi

# Categorize TMs by type
time python3 Code/IO_Categorize.py ${OUT_DIR}/out.pb --out-dir=${OUT_DIR}

# Create file (empty) to indicate that this array job succeeded.
touch ${OUT_DIR}/success

echo Success
