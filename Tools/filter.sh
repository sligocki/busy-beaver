#!/bin/bash
#
# Example:
#  Tools/filter.sh data/bb/4x2/ rev_eng Code/Reverse_Engineer_Filter.py
#  Tools/filter.sh data/bb/4x2/ ctl2_mb6 Code/CTL_Filter.py --type=CTL2 --max-block-size=6
#  Tools/filter.sh data/bb/4x2/ b2_1k Code/Enumerate.py --block-size=2 --max-loops=1_000 --lin-steps=0 --no-ctl --no-reverse-engineer
#  Tools/filter.sh data/bb/4x2/ 10k Code/Enumerate.py --max-loops=10_000 --lin-steps=0 --no-ctl --no-reverse-engineer
set -u
set -e
set -x

ROOT_DIR=$1
shift
SUBDIR=$1
shift

WORK_DIR=${ROOT_DIR}/${SUBDIR}/
rm -rf ${WORK_DIR}
mkdir -p ${WORK_DIR}

# Pull in holdouts (from previous filter)
cp ${ROOT_DIR}/unknown.pb ${WORK_DIR}/in.pb

# Run main filter command
time "$@" --infile=${WORK_DIR}/in.pb --outfile=${WORK_DIR}/out.pb

# Categorize outputs
time Code/IO_Categorize.py ${WORK_DIR}/out.pb --out-dir=${WORK_DIR}/

# Update for next filter
cp ${WORK_DIR}/unknown.pb ${ROOT_DIR}/unknown.pb

# Human readable stuff
time Code/TM_Analyze.py ${WORK_DIR}/out.pb
# Only convert to text if it's reasonably small.
if [[ "$(wc -c < ${ROOT_DIR}/unknown.pb)" < 1000000 ]]; then
  Code/IO_Convert.py ${ROOT_DIR}/unknown.{pb,txt}
fi
