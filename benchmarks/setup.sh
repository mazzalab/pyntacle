#!/bin/bash
# Prepares this machine for the benchmark. run.sh calls it the first time;
# it can also be run by hand, from any directory:
#
#   bash benchmarks/setup.sh
#
# It creates the two conda environments if they do not exist (Pyntacle 2 from
# environment.yml, Pyntacle 1.3.2 from the bfxcss channel), compiles
# Pyntacle 2's extensions in place, generates the networks of every config
# that are not in benchmarks/data yet, and marks the setup as done.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
rm -f "$REPO/benchmarks/results/.setup_ok"
command -v conda > /dev/null || { echo "conda is not on the PATH: install Miniconda or Miniforge first"; exit 1; }
eval "$(conda shell.bash hook)"
: "${PYNTACLE_ENV:=pyntacle}"
: "${PYNTACLE_OLD_ENV:=pyntacle_old}"

if ! conda env list | grep -q "^$PYNTACLE_OLD_ENV "; then
    conda create -y -n "$PYNTACLE_OLD_ENV" -c conda-forge -c bfxcss python=3.7 pyntacle=1.3.2
fi
if ! conda env list | grep -q "^$PYNTACLE_ENV "; then
    conda env create -n "$PYNTACLE_ENV" -f "$REPO/environment.yml"
fi
source "$REPO/benchmarks/env.sh"
"$PYNTACLE_OLD_BIN" --version

conda activate "$PYNTACLE_ENV"
cd "$REPO"
python setup.py build_ext --inplace
cd benchmarks
for cfg in configs/*.json; do
    python bench.py prepare "$cfg"
done
mkdir -p results
date -Is > results/.setup_ok
echo "setup ok"
echo "PYNTACLE_PYTHON=$PYNTACLE_PYTHON"
echo "PYNTACLE_OLD_BIN=$PYNTACLE_OLD_BIN"
