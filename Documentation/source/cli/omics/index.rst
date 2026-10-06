omics
=====

``omics`` turns a raw omics matrix and its sample metadata into one network per
sample group, written in the format that every other Pyntacle command reads.
It runs the preprocessing and inference of the colorectal cancer case study
on any dataset.

Two pipelines are available:

* **transcriptomics**: bulk RNA-seq counts → median-of-ratios normalisation →
  data-driven gene selection → expression gate → Ledoit–Wolf partial
  correlations → permutation FDR;
* **metagenomics**: relative abundances or read counts → prevalence panel →
  closure, multiplicative zero replacement, centred log-ratio → graphical
  lasso with the penalty chosen by StARS.

Each step, and the reference behind it, is described in
:doc:`../../omics/omics`.

.. note::

   ``omics`` needs scikit-learn and statsmodels, which the rest of Pyntacle
   does not use. ``environment.yml`` installs both; in another environment:

   .. code-block:: console

      pip install scikit-learn statsmodels      # add mygene for --biotype mygene

   Without them, the other commands work unchanged and ``omics`` stops with
   the install command.

Synopsis
--------
.. code-block:: console

   pyntacle omics transcriptomics -i counts.tsv -m metadata.tsv --group-col condition -o out/ [OPTIONS]
   pyntacle omics transcriptomics -i counts.tsv --tcga -o out/ [OPTIONS]
   pyntacle omics metagenomics    -i abundances.tsv -m metadata.tsv --group-col condition -o out/ [OPTIONS]

Input
-----

* **Matrix**: features (genes or taxa) × samples, first column = feature id,
  tab-separated (comma-separated if the name ends in ``.csv``), optionally
  compressed (``.gz``, ``.bz2``, ``.xz``, ``.zip``). The transposed layout is
  accepted: the orientation is taken from the axis that carries the sample
  ids. Every feature id must be unique and no value may be missing.
* **Metadata**: one row per sample, first column = sample id, one column with
  the group (``--group-col``). Each sample id must appear once. Samples
  missing from either table, or without a group, are left out and counted in
  the report. Every group needs at least 5 samples.
* **Transcriptomics values**: raw counts, or ``log2(count + 1)`` as
  distributed by UCSC Xena; the scale is detected. Normalised values (TPM,
  FPKM, their logarithms, z-scores) are refused.
* **Metagenomics values**: relative abundances, as fractions or percentages,
  or read counts; closure makes them equivalent. Log- or CLR-transformed
  tables (negative values) are refused: the pipeline applies the CLR itself.

Microbiome profilers
~~~~~~~~~~~~~~~~~~~~

The metagenomics pipeline reads the tables of the common profilers as they
are written:

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Profiler
     - File
     - What ``omics`` does with it
   * - MetaPhlAn 3 and 4
     - Table merged with ``merge_metaphlan_tables.py``
     - Skips the database line, ignores the ``NCBI_tax_id`` column, and keeps
       the rank given with ``--rank`` (required: the table holds every rank).
       ``UNCLASSIFIED`` is left out. Taxa are named by their last level, such
       as ``g__Bacteroides``.
   * - QIIME 2
     - Feature table exported to TSV:
       ``qiime tools export`` then ``biom convert --to-tsv``
     - Skips the ``# Constructed from biom file`` line and ignores a
       ``taxonomy`` column. A table collapsed to one level
       (``qiime taxa collapse``) is detected as that rank; ``Unassigned`` is
       left out.
   * - QIIME 2
     - Metadata file
     - Reads ``sample-id`` or ``#SampleID`` as the id column and skips the
       ``#q2:types`` row.
   * - Any other tool
     - Taxa × samples table
     - Used as it is; ``--rank`` applies only if the feature ids are
       lineages (``k__…|p__…`` or ``d__…;p__…``).

``.qza`` and ``.biom`` files are binary: ``omics`` stops and prints the
command that exports them. The sample names of a merged MetaPhlAn table come
from the profile file names and must match the metadata ids. A table of
amplicon sequence variants (ASVs) works, but its many sparse features are
better collapsed to genus first, so that the network links taxa that can be
interpreted.

Options
-------
.. list-table::
   :header-rows: 1
   :widths: 20 8 7 14 14 37

   * - Option
     - Required
     - Type
     - Default
     - Pipeline
     - Help
   * - ``-i``, ``--inputFile``
     - Yes
     - str
     - \ 
     - both
     - Feature × sample matrix (sample × feature is detected from the sample ids)
   * - ``-m``, ``--metadata``
     - Yes [1]_
     - str
     - \ 
     - both
     - Sample metadata table; first column = sample id
   * - ``--group-col``
     - Yes [1]_
     - str
     - \ 
     - both
     - Metadata column with the sample group; one network is built per group
   * - ``--groups``
     - No
     - str
     - all
     - both
     - Comma-separated groups to keep (with ``--tcga``: the group names of ``--tcga-types``)
   * - ``-o``, ``--outdir``
     - Yes
     - str
     - \ 
     - both
     - Output directory (created if missing)
   * - ``--prefix``
     - No
     - str
     - input file name
     - both
     - Prefix of every output file; the default drops the table and compression extensions
   * - ``--sep``
     - No
     - str
     - ``,`` for .csv, tab otherwise
     - both
     - Field separator of the matrix and the metadata
   * - ``--covariates``
     - No
     - str
     - \ 
     - both
     - Comma-separated metadata columns (numeric or categorical) regressed out of every feature, within each group
   * - ``--seed``
     - No
     - int
     - 20260731 / 0
     - both
     - Random seed of the permutations (transcriptomics) or of the StARS subsamples (metagenomics); between 0 and 2\ :sup:`32` − 1
   * - ``--save-stages``
     - No
     - bool
     - False
     - both
     - Also write the intermediate matrices
   * - ``--input-scale``
     - No
     - str
     - auto
     - transcriptomics
     - ``auto``, ``counts`` or ``log2p1``; ``auto`` detects it (UCSC Xena STAR counts are log2(count + 1))
   * - ``--tcga``
     - No
     - bool
     - False
     - transcriptomics
     - Groups from the TCGA barcodes, one sample per patient and type; replaces ``-m`` and ``--group-col`` (``-m`` is still read for ``--covariates``)
   * - ``--tcga-types``
     - No
     - str
     - ``01:tumor,11:normal``
     - transcriptomics
     - With ``--tcga``: sample type codes to keep and their group names, e.g. ``01:primary,06:metastatic``
   * - ``--biotype``
     - No
     - str
     - \ 
     - transcriptomics
     - ``mygene`` (online query) or an annotation file with columns ``gene,symbol,type_of_gene``: keep protein-coding and ncRNA genes
   * - ``--drop-sex-genes``
     - No
     - bool
     - False
     - transcriptomics
     - Remove 16 sex-linked genes (XIST, RPS4Y1, …); needs ``--biotype`` for symbols
   * - ``--gate-alpha``
     - No
     - float
     - 0.05
     - transcriptomics
     - Significance of the expression-bias test that stops the gate; in (0, 1)
   * - ``--gate-top``
     - No
     - int
     - 100
     - transcriptomics
     - Strongest edges inspected by the gate; lower it for panels of a few hundred genes
   * - ``--gate-min-genes``
     - No
     - int
     - 300
     - transcriptomics
     - Stop raising the gate below this many genes
   * - ``--fdr``
     - No
     - float
     - 0.001
     - transcriptomics
     - False discovery rate of the edges; in (0, 1)
   * - ``--n-perm``
     - No
     - int
     - 3
     - transcriptomics
     - Permutations of the null distribution
   * - ``--rank``
     - No [2]_
     - str
     - \ 
     - metagenomics
     - ``kingdom``, ``phylum``, ``class``, ``order``, ``family``, ``genus``, ``species`` or ``strain``: rank analysed when the feature ids are lineages
   * - ``--prevalence``
     - No
     - str
     - auto
     - metagenomics
     - Prevalence threshold of the taxon panel, in (0, 1], or ``auto``
   * - ``--stars-beta``
     - No
     - float
     - 0.10
     - metagenomics
     - StARS instability bound; in (0, 0.5)
   * - ``--n-sub``
     - No
     - int
     - 50
     - metagenomics
     - StARS subsamples

.. [1] Not with ``transcriptomics --tcga``, where the groups come from the barcodes.
.. [2] Required when the table lists several ranks, as a merged MetaPhlAn table does.

An option of the other pipeline, an option that conflicts with another (such
as ``--group-col`` with ``--tcga``) or a value out of range stops the command
before any file is read.

What is data-driven
-------------------

The pipelines are not free of parameters. Each value in the report is
labelled with where it came from:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Value
     - Kind
     - How it is chosen
   * - Input scale
     - data-driven
     - integers → counts; non-integers ≤ 50 that transform back to integers → log2(count + 1)
   * - Taxonomic rank
     - data-driven
     - the only rank of the table (``user`` with ``--rank``)
   * - Expressed / highly variable genes
     - data-driven
     - two-component Gaussian mixtures (no threshold)
   * - Expression gate
     - data-driven
     - first mean-expression quantile at which the strongest edges are no longer enriched in weakly expressed genes
   * - Shrinkage intensity
     - data-driven
     - Ledoit–Wolf analytical estimate
   * - Prevalence threshold
     - data-driven
     - lowest threshold (0.05 to 0.50, step 0.05) leaving fewer taxa than samples in the smallest group
   * - Graphical lasso penalty
     - data-driven
     - StARS, largest stable network under the instability bound
   * - FDR, permutations, StARS bound, seeds
     - default
     - conventional values, overridable by flag

Output
------

For every group ``<g>`` (lower-case, with each run of other characters than
letters and digits replaced by ``_``):

``<prefix>_<g>.tsv``
   Edge list with header ``N1 N2 Weight``. **Weight is the signed partial
   correlation** *r*. Read it with ``-t edgelist -w -wt signed``: \|r\| is the
   strength of the tie, 1/\|r\| the length used by shortest-path measures,
   and the sign is kept (see :doc:`/weights`). Nodes without edges are not
   written; a group with no edge gives a file with the header only.

``<prefix>_<g>.graphml``
   The same edges with the attributes ``assoc_weight`` (signed partial
   correlation), ``abs_r``, ``q_value`` (transcriptomics) and
   ``n_copresent`` (metagenomics: the samples of the group in which both
   taxa are present). Node
   attributes: ``mean_log2_expr``, plus ``symbol`` and ``biotype`` with
   ``--biotype`` (transcriptomics); ``mean_rel_abundance`` (mean share
   of the sample total, 0–1, whatever the input unit) and ``prevalence``
   (metagenomics).

``<prefix>_report.tsv`` and ``<prefix>_report.json``
   Every value used, with its kind (data-driven / default / user), the
   diagnostics behind the data-driven choices (gate table, StARS instability
   curve, prevalence grid, size factors), warnings, and package versions.

With ``--save-stages``, the intermediate matrices ``<prefix>_<g>_<stage>.tsv.gz``:
``log_norm`` and ``final`` (transcriptomics), ``clr`` (metagenomics).

Examples
--------

A generic dataset, then the key players of the tumour network:

.. code-block:: console

   pyntacle omics metagenomics -i relabund.tsv -m samples.tsv \
       --group-col condition -o nets/
   pyntacle keyplayer kp-finder -t edgelist -w -wt signed \
       -i nets/relabund_tumor.tsv -k 2 -oper all -a greedy -o kp/

A merged MetaPhlAn table, analysed at genus rank:

.. code-block:: console

   merge_metaphlan_tables.py profiles/*.txt > merged_abundance_table.txt
   pyntacle omics metagenomics -i merged_abundance_table.txt -m samples.tsv \
       --group-col condition --rank genus -o nets/

A QIIME 2 feature table collapsed to genus (level 6):

.. code-block:: console

   qiime taxa collapse --i-table table.qza --i-taxonomy taxonomy.qza \
       --p-level 6 --o-collapsed-table genus.qza
   qiime tools export --input-path genus.qza --output-path genus/
   biom convert -i genus/feature-table.biom -o genus.tsv --to-tsv
   pyntacle omics metagenomics -i genus.tsv -m sample-metadata.tsv \
       --group-col condition -o nets/

TCGA metastatic melanoma against primary tumours:

.. code-block:: console

   pyntacle omics transcriptomics -i TCGA-SKCM.star_counts.tsv --tcga \
       --tcga-types 01:primary,06:metastatic -o skcm/

Adjusting for covariates (age and a categorical batch):

.. code-block:: console

   pyntacle omics transcriptomics -i counts.tsv -m samples.tsv \
       --group-col condition --covariates age,batch -o nets/

The colorectal cancer case study (TCGA-COAD from UCSC Xena, TCMA microbiome):

.. code-block:: console

   # transcriptome: 1,715 nodes / 3,148 edges (tumour), 824 / 3,371 (normal)
   pyntacle omics transcriptomics -i TCGA-COAD.star_counts.tsv --tcga \
       --biotype mygene_biotype_cache_hvg.csv --drop-sex-genes -o coad/ --prefix coad

   # microbiome, genus: the automatic prevalence threshold is 0.15
   pyntacle omics metagenomics -i bacteria.sample.relabund.genus.txt \
       -m sample_metadata_genus.txt --group-col Definition \
       --groups "Primary Solid Tumor,Solid Tissue Normal" -o tcma/ --prefix genus

   # microbiome, family: same threshold as genus, applied uniformly
   pyntacle omics metagenomics -i bacteria.sample.relabund.family.txt \
       -m sample_metadata_family.txt --group-col Definition \
       --groups "Primary Solid Tumor,Solid Tissue Normal" -o tcma/ --prefix family \
       --prevalence 0.15

.. tip::

   Analysing the same samples at several taxonomic ranks? Let the automatic
   rule choose the threshold on one rank and pass it with ``--prevalence`` to
   the others, so that all ranks share one threshold.
