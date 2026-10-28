# Points the benchmark at the two Pyntacle installations. Source it, from any
# directory, before running bench.py or submitting jobs:
#
#   source benchmarks/env.sh
#
# By default the two installations are the conda environments made by
# benchmarks/setup.sh: PYNTACLE_ENV (default "pyntacle", Pyntacle 2) and
# PYNTACLE_OLD_ENV (default "pyntacle_old", Pyntacle 1.3.2). To use other
# installations, export the two paths yourself before sourcing:
#
#   export PYNTACLE_PYTHON=/path/to/env/bin/python       # Python with Pyntacle 2's dependencies
#   export PYNTACLE_OLD_BIN=/path/to/old_env/bin/pyntacle  # the pyntacle 1.3.2 command

: "${PYNTACLE_ENV:=pyntacle}"
: "${PYNTACLE_OLD_ENV:=pyntacle_old}"
if [ -z "${PYNTACLE_PYTHON:-}" ] || [ -z "${PYNTACLE_OLD_BIN:-}" ]; then
    _conda_base=$(conda info --base)
    : "${PYNTACLE_PYTHON:=$_conda_base/envs/$PYNTACLE_ENV/bin/python}"
    : "${PYNTACLE_OLD_BIN:=$_conda_base/envs/$PYNTACLE_OLD_ENV/bin/pyntacle}"
    unset _conda_base
fi
export PYNTACLE_PYTHON PYNTACLE_OLD_BIN
