"""`pyntacle omics` arguments -> pipeline -> files."""
import os
import sys

from . import require
from .export import PYNTACLE_FLAGS, safe_name, write_network
from .loader import check_groups, load_inputs, read_table
from .provenance import Provenance

# options whose explicit use is recorded as "user" rather than "default"
_TX = ("gate_alpha", "gate_top", "gate_min_genes", "fdr", "n_perm", "seed")
_MG = ("stars_beta", "n_sub", "seed")


def _given(argv):
    """Long option names the user typed, as argparse dests."""
    return frozenset(a[2:].split("=")[0].replace("-", "_") for a in argv if a.startswith("--"))


def _metadata(args):
    meta = read_table(args.metadata, args.sep)
    meta.index = meta.index.astype(str)
    return meta


def run_omics(args, argv=None):
    require()
    given = _given(sys.argv if argv is None else argv)
    prov = Provenance(args.subcommand)
    groups = args.groups.split(",") if args.groups else None
    covariates = args.covariates.split(",") if args.covariates else None
    if covariates and not args.metadata:
        raise SystemExit("ERROR: --covariates needs --metadata")
    meta = None

    if args.subcommand == "transcriptomics" and args.tcga:
        from .transcriptomics.tcga import tcga_groups
        X = read_table(args.inputFile, args.sep)
        X.columns = X.columns.astype(str)
        labels, dropped = tcga_groups(list(X.columns))
        if groups:
            labels = labels[labels.isin(groups)]
        X = X[labels.index].astype(float)
        prov.record("input", "tcga_dropped_other_type", len(dropped["other_type"]), "data-driven",
                    "sample types other than 01/11")
        prov.record("input", "tcga_dropped_duplicate", len(dropped["duplicate"]), "data-driven",
                    "extra aliquots of the same patient")
        if covariates:
            meta = _metadata(args)
    else:
        if not args.metadata or not args.group_col:
            raise SystemExit("ERROR: --metadata and --group-col are required"
                             + (" (or --tcga)" if args.subcommand == "transcriptomics" else ""))
        X, labels = load_inputs(args.inputFile, args.metadata, args.group_col, groups, args.sep, prov)
        if covariates:
            meta = _metadata(args)
    check_groups(labels)
    for g, n in labels.value_counts().items():
        prov.record("input", "n_" + str(g), int(n), "data-driven")

    if args.subcommand == "transcriptomics":
        from . import transcriptomics
        from .transcriptomics import select
        annotation = None
        if args.biotype == "mygene":
            annotation = select.query_mygene(X.index)
        elif args.biotype:
            annotation = select.load_annotation(args.biotype)
        result = transcriptomics.run(
            X, labels, prov=prov, meta=meta, input_scale=args.input_scale, annotation=annotation,
            drop_sex_genes=args.drop_sex_genes, covariates=covariates, gate_alpha=args.gate_alpha,
            gate_top=args.gate_top, gate_min_genes=args.gate_min_genes, fdr=args.fdr,
            n_perm=args.n_perm, seed=20260731 if args.seed is None else args.seed,
            user_set=frozenset(k for k in _TX if k in given))
    else:
        from . import metagenomics
        result = metagenomics.run(
            X, labels, prov=prov, meta=meta, prevalence=args.prevalence, covariates=covariates,
            stars_beta=args.stars_beta, n_sub=args.n_sub, seed=0 if args.seed is None else args.seed,
            user_set=frozenset(k for k in _MG if k in given))

    prefix = args.prefix or os.path.basename(args.inputFile).split(".")[0]
    os.makedirs(args.outdir, exist_ok=True)
    written = {}
    for g, res in result.items():
        written[g] = write_network(res["edges"], res["nodes"], args.outdir, prefix, g)
        print("{}: {} nodes, {} edges -> {}".format(g, written[g]["n_nodes"], written[g]["n_edges"],
                                                    written[g]["edgelist"]))
        if args.save_stages:
            for name, df in res["stages"].items():
                df.to_csv(os.path.join(args.outdir, "{}_{}_{}.tsv.gz".format(
                    prefix, safe_name(g), name)), sep="\t")
    prov.write(args.outdir, prefix)
    for w in prov.warnings:
        print("WARNING: " + w)
    print("Report: " + os.path.join(args.outdir, prefix + "_report.tsv"))
    print("Weights are signed partial correlations; analyse the networks with "
          "`pyntacle <command> -t edgelist -i <network>.tsv {}`".format(PYNTACLE_FLAGS))
    return written
