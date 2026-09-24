#!/bin/bash
# One-time (and after every rsync): build the new tool's Cython extensions for
# this CPU, make sure the old tool's env exists, and generate the graph corpus
# once, before shards start in parallel and race on the same files.
#
#   bash benchmarks/pbs/setup_cluster.sh hpc-paper
set -euo pipefail
PROFILE=${1:-hpc-paper}
REPO=/data/data_storage/research/Mangoni_Manuel/pyntacle_final
source /home/04203147/miniconda3/etc/profile.d/conda.sh

if ! conda env list | grep -q "^pyntacle_old "; then
    conda create -y -n pyntacle_old -c conda-forge -c bfxcss python=3.7 pyntacle=1.3.2
fi
conda activate pyntacle_old
pyntacle --version

conda activate graphtacle_debug
cd "$REPO"
python -c "import psutil" 2>/dev/null || pip install psutil
python setup.py build_ext --inplace
cd benchmarks
python bench.py plan "configs/$PROFILE.json" --shards 5
python bench.py prepare "configs/$PROFILE.json"
