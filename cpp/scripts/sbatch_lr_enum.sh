#!/bin/bash
#SBATCH -J lr_enum
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 24
#SBATCH -t 24:00:00
#SBATCH -o lr_enum-%J.txt

set -e
set -u

time bash scripts/lr_enum_local_parallel.sh "$@"

echo Success
