#!/bin/bash
#SBATCH -J lr
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 24
#SBATCH -t 24:00:00
#SBATCH -p long
#SBATCH -o lr_enum-%A_%a.txt

set -e
set -u

time bash scripts/lr_enum_local_parallel.sh "$@"

echo Success
