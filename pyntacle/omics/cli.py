"""`pyntacle omics` arguments -> pipeline -> files."""
import functools
import os
import sys

from . import require
from .export import PYNTACLE_FLAGS, safe_name, write_network
from .loader import COMPRESSED, check_groups, check_matrix, load_inputs, read_metadata, read_table
from .provenance import Provenance

# options whose explicit use is recorded as "user" rather than "default"
_TX = ("gate_alpha", "gate_top", "gate_min_genes", "fdr", "n_perm", "seed")
_MG = ("stars_beta", "n_sub", "seed")
# options that belong to one pipeline only
_ONLY = {"transcriptomics": ("input_scale", "tcga", "tcga_types", "biotype", "drop_sex_genes",
                             "gate_alpha", "gate_top", "gate_min_genes", "fdr", "n_perm"),
         "metagenomics": ("rank", "prevalence", "stars_beta", "n_sub")}
_TABLE_EXT = (".tsv", ".csv", ".txt", ".tab")


def _given(argv):
    """Long option names the user typed, as argparse dests."""
    return frozenset(a[2:].split("=")[0].replace("-", "_") for a in argv if a.startswith("--"))


def _flag(dest):
    return "--" + dest.replace("_", "-")


def _check_options(args, given):
    """Conflicts argparse cannot see, refused before any file is read."""
    for pipeline, dests in _ONLY.items():
        if args.subcommand != pipeline:
            wrong = [_flag(d) for d in dests if d in given]
            if wrong:
                raise SystemExit("ERROR: {} only appl{} to {}".format(
                    ", ".join(wrong), "ies" if len(wrong) == 1 else "y", pipeline))
    if args.tcga:
        if args.group_col:
            raise SystemExit("ERROR: --group-col does not apply with --tcga: "
                             "the groups come from the barcodes (--tcga-types)")
        if args.metadata and not args.covariates:
            raise SystemExit("ERROR: with --tcga, -m is read only for --covariates")
    elif "tcga_types" in given:
        raise SystemExit("ERROR: --tcga-types needs --tcga")
    elif not args.metadata or not args.group_col:
        raise SystemExit("ERROR: --metadata and --group-col are required"
                         + (" (or --tcga)" if args.subcommand == "transcriptomics" else ""))
    if args.covariates and not args.metadata:
        raise SystemExit("ERROR: --covariates needs --metadata")
    if args.drop_sex_genes and not args.biotype:
        raise SystemExit("ERROR: --drop-sex-genes needs gene symbols: pass --biotype")


def _metadata(args):
    return read_metadata(args.metadata, args.sep)


def _prefix(path):
    """Input file name without its table and compression extensions."""
    name = os.path.basename(path)
    for exts in (COMPRESSED, _TABLE_EXT):
        for ext in exts:
            if name.lower().endswith(ext):
                name = name[: -len(ext)]
                break
    return name


def _tcga_inputs(args, given, groups, covariates, prov):
    from .transcriptomics.tcga import orient_barcodes, parse_types, tcga_groups
    codes = parse_types(args.tcga_types)
    if groups:
        unknown = set(groups) - set(codes.values())
        if unknown:
            raise SystemExit("ERROR: --groups not among the --tcga groups ({}): {}".format(
                ", ".join(codes.values()), ", ".join(sorted(unknown))))
    X = orient_barcodes(read_table(args.inputFile, args.sep))
    X.columns = X.columns.astype(str)
    labels, dropped = tcga_groups(list(X.columns), codes)
    if groups:
        labels = labels[labels.isin(groups)]
    try:
        X = X[labels.index].astype(float)
    except ValueError:
        raise SystemExit("ERROR: non-numeric values in the matrix columns of the samples")
    check_matrix(X)
    kept = "/".join(codes)
    prov.record("input", "tcga_types", args.tcga_types, "user" if "tcga_types" in given else "default")
    prov.record("input", "tcga_dropped_other_type", len(dropped["other_type"]), "data-driven",
                "sample types other than " + kept)
    prov.record("input", "tcga_dropped_duplicate", len(dropped["duplicate"]), "data-driven",
                "extra aliquots of the same patient")
    meta = None
    if covariates:
        meta = _metadata(args)
        missing = [s for s in labels.index if s not in meta.index]
        if missing:
            raise SystemExit("ERROR: {} sample(s) missing from the metadata, needed for --covariates: {}"
                             .format(len(missing), ", ".join(missing[:5])))
    return X, labels, meta


def run_omics(args, argv=None):
    require()
    given = _given(sys.argv if argv is None else argv)
    _check_options(args, given)
    prov = Provenance(args.subcommand)
    groups = args.groups.split(",") if args.groups else None
    covariates = args.covariates.split(",") if args.covariates else None

    if args.subcommand == "transcriptomics" and args.tcga:
        X, labels, meta = _tcga_inputs(args, given, groups, covariates, prov)
    else:
        features = None
        if args.subcommand == "metagenomics":
            from .metagenomics.taxonomy import select_rank
            features = functools.partial(select_rank, rank=args.rank, prov=prov)
        X, labels = load_inputs(args.inputFile, args.metadata, args.group_col, groups, args.sep, prov,
                                features=features)
        meta = _metadata(args) if covariates else None
    if covariates:
        missing = [c for c in covariates if c not in meta.columns]
        if missing:
            raise SystemExit("ERROR: --covariates not in metadata: " + ", ".join(missing))
    check_groups(labels)
    files = {}
    for g in labels.unique():
        files.setdefault(safe_name(g), []).append(g)
    clash = [" / ".join(v) for v in files.values() if len(v) > 1]
    if clash:
        raise SystemExit("ERROR: groups that would write the same file: " + "; ".join(clash))
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

    prefix = args.prefix or _prefix(args.inputFile)
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
