#!/bin/bash
# Submit a profile's shards, each asking only for the CPUs, memory and
# walltime in the config's "pbs" block (no whole-node exclusivity), spread
# round-robin over the given hosts. hpc02-hpc06 are identical CPUs; hpc01 is
# the login node and is never used; hpc09-11 have different CPUs, which would
# make times from different shards incomparable.
#
# Without AFTER, a small setup job (build, graph corpus) is submitted first on
# the first host and every shard waits for it to succeed:
#   bash benchmarks/pbs/submit.sh hpc-paper 4 hpc03 hpc04 hpc05
# With AFTER=<jobid>, no setup is submitted and the shards wait for that job:
#   AFTER=30470.hpcmaster bash benchmarks/pbs/submit.sh hpc-paper-threads 1 hpc05
set -euo pipefail
PROFILE=$1; SHARDS=$2; shift 2
HOSTS=("$@")
[ ${#HOSTS[@]} -gt 0 ] || { echo "usage: submit.sh PROFILE SHARDS HOST..."; exit 1; }
for h in "${HOSTS[@]}"; do
    if [ "$h" = "hpc01" ]; then echo "refusing hpc01 (login node)"; exit 1; fi
done
REPO=/data/data_storage/research/Mangoni_Manuel/pyntacle_final
CONFIG=$REPO/benchmarks/configs/$PROFILE.json
LOGDIR=$REPO/benchmarks/results/$PROFILE/pbs_logs
mkdir -p "$LOGDIR"
read -r NCPUS MEM WALL < <(python3 -c "import json,sys; p=json.load(open(sys.argv[1]))['pbs']; print(p['ncpus'], p['mem'], p['walltime'])" "$CONFIG")

if [ -z "${AFTER:-}" ]; then
    rm -f "$REPO/benchmarks/results/.setup_ok"
    AFTER=$(qsub -N pynsetup -l "select=1:ncpus=2:mem=4gb:host=${HOSTS[0]}" -l walltime=01:00:00 \
                 -j oe -o "$REPO/benchmarks/results/setup_$PROFILE.log" \
                 -v "PROFILE=$PROFILE" "$REPO/benchmarks/pbs/setup_cluster.sh")
    echo "setup: $AFTER"
fi
[ -n "$AFTER" ] || { echo "no setup job id: not submitting shards"; exit 1; }

TAG=pb; [[ $PROFILE == *threads* ]] && TAG=pt
for ((i = 0; i < SHARDS; i++)); do
    h=${HOSTS[$((i % ${#HOSTS[@]}))]}
    jid=$(qsub -N "${TAG}${i}of${SHARDS}" -W "depend=afterok:$AFTER" \
               -l "select=1:ncpus=$NCPUS:mem=$MEM:host=$h" -l "walltime=$WALL" \
               -o "$LOGDIR/shard_${i}of${SHARDS}_$h.log" \
               -v "SHARD=$i/$SHARDS,PROFILE=$PROFILE" \
               "$REPO/benchmarks/pbs/bench_shard.pbs")
    echo "shard $i/$SHARDS on $h ($NCPUS cpus, $MEM): $jid"
done
