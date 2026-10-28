#!/bin/bash
# Runs the benchmark on this machine, from any directory:
#
#   bash benchmarks/run.sh figures         # tables and figures of the paper from the shipped results; runs nothing
#   bash benchmarks/run.sh smoke           # both versions on networks of 40-120 nodes, a few minutes
#   bash benchmarks/run.sh paper           # Table 1 and Supplementary Figs S2-S7
#   bash benchmarks/run.sh paper-threads   # Supplementary Figs S8-S9
#
# The first time, it sets up the machine (setup.sh). New runs write to
# benchmarks/results/local/<profile>; the shipped results in
# benchmarks/results/<profile> are left as they are. An interrupted run,
# started again, continues where it stopped.
set -euo pipefail
PROFILE=${1:-}
case "$PROFILE" in
    figures|smoke|paper|paper-threads) ;;
    *) echo "usage: run.sh figures|smoke|paper|paper-threads"; exit 1 ;;
esac
BENCH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$BENCH"
[ -f results/.setup_ok ] || bash setup.sh
source env.sh
PY=$PYNTACLE_PYTHON

if [ "$PROFILE" = figures ]; then
    for out in results/paper results/paper-threads; do
        "$PY" bench.py collect "$out"
    done
    "$PY" plot_results.py results/paper
    "$PY" plot_threads.py results/paper-threads
    echo "figures in results/paper/plots and results/paper-threads/plots"
    exit 0
fi

# CPUs and memory the profile keeps busy at once (slots, mem_budget_mb)
read -r SLOTS BUDGET < <("$PY" -c "import json,sys; c=json.load(open(sys.argv[1])); print(c.get('slots', 1), c.get('mem_budget_mb', 0))" "configs/$PROFILE.json")
CPUS=$(nproc)
MEM_MB=$(awk '/MemAvailable/ {print int($2 / 1024)}' /proc/meminfo)
if [ "$CPUS" -lt "$SLOTS" ]; then
    echo "warning: $PROFILE uses up to $SLOTS CPUs at once, this machine has $CPUS"
fi
if [ "$MEM_MB" -lt "$BUDGET" ]; then
    echo "warning: $PROFILE budgets $BUDGET MB of memory, $MEM_MB MB are available"
fi

OUT=results/local/$PROFILE
"$PY" bench.py run "configs/$PROFILE.json" --out "$OUT"
"$PY" bench.py collect "$OUT"
"$PY" bench.py parity "$OUT"
case "$PROFILE" in
    paper) "$PY" plot_results.py "$OUT" ;;
    paper-threads) "$PY" plot_threads.py "$OUT" ;;
esac
echo "results in $OUT"
