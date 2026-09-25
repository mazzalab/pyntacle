#!/bin/bash
# Run by submit.sh as a small PBS job before the shards (it can also be run by
# hand): build the new tool's Cython extensions for this CPU, make sure the old
# tool's env exists, generate the graph corpus once so shards never race on
# the same files, then mark the setup as done.
#PBS -j oe
set -euo pipefail
PROFILE=${PROFILE:-${1:-hpc-paper}}
REPO=/data/data_storage/research/Mangoni_Manuel/pyntacle_final
rm -f "$REPO/benchmarks/results/.setup_ok"
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
for cfg in configs/hpc-paper*.json; do
    python bench.py plan "$cfg" --shards 1
    python bench.py prepare "$cfg"
done
mkdir -p results
date -Is > results/.setup_ok
echo "setup ok ($PROFILE)"
