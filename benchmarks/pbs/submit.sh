#!/bin/bash
# Submit one shard per node. hpc02-hpc06 are identical (32 cores, ~504 GB);
# hpc01 is the login node and is never used; hpc09-11 have different CPUs,
# which would make times from different shards incomparable.
#
#   bash benchmarks/pbs/submit.sh hpc-paper hpc02 hpc03 hpc04 hpc05 hpc06
set -euo pipefail
PROFILE=$1; shift
HOSTS=("$@")
N=${#HOSTS[@]}
REPO=/data/data_storage/research/Mangoni_Manuel/pyntacle_final
LOGDIR=$REPO/benchmarks/results/$PROFILE/pbs_logs
mkdir -p "$LOGDIR"
for i in "${!HOSTS[@]}"; do
    h=${HOSTS[$i]}
    if [ "$h" = "hpc01" ]; then echo "refusing hpc01 (login node)"; exit 1; fi
    qsub -N "pynbench_${i}of${N}" \
         -l "select=1:ncpus=32:mem=480gb:host=$h" \
         -o "$LOGDIR/shard_${i}of${N}_$h.log" \
         -v "SHARD=$i/$N,PROFILE=$PROFILE" \
         "$REPO/benchmarks/pbs/bench_shard.pbs"
done
