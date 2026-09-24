omics
=====

``omics`` turns a raw omics matrix and its sample metadata into one network per
sample group, written in the format every other Pyntacle command reads. It is
the preprocessing and inference code of the colorectal cancer case study,
generalised to any dataset.

Two pipelines are available:

* **transcriptomics** — bulk RNA-seq counts → median-of-ratios normalisation →
  data-driven gene selection → expression gate → Ledoit–Wolf partial
  correlations → permutation FDR;
* **metagenomics** — relative abundances → prevalence panel → closure,
  multiplicative zero replacement, centred log-ratio → graphical lasso with
  the penalty chosen by StARS.

Every step and its reference is described in :doc:`../../omics/omics`.

.. note::

   ``omics`` needs two packages that the rest of Pyntacle does not:

   .. code-block:: console

      pip install scikit-learn statsmodels      # add mygene for --biotype mygene

   Without them the other commands work unchanged and ``omics`` stops with the
   install command.

Synopsis
--------
.. code-block:: console

   python3 main.py omics transcriptomics -i counts.tsv -m metadata.tsv --group-col condition -o out/ [OPTIONS]
   python3 main.py omics metagenomics    -i relabund.tsv -m metadata.tsv --group-col condition -o out/ [OPTIONS]

Input
-----

* **Matrix** — features (genes or taxa) × samples, first column = feature id.
  The transposed layout is accepted: the orientation is taken from whichever
  axis carries the metadata sample ids.
* **Metadata** — one row per sample, first column = sample id, one column
  with the group (``--group-col``). Samples missing from either table, or
  without a group, are dropped and counted in the report. Every group needs at
  least 5 samples.
* **Transcriptomics values** — raw counts or ``log2(count + 1)``; the scale
  is detected. Normalised data (TPM, FPKM, z-scores) are refused.
* **Metagenomics values** — relative abundances, as fractions or percentages
  (closure makes them equivalent), or raw read counts.

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
     - Feature × sample matrix (sample × feature is detected from the metadata ids). TSV, or CSV by extension; may be gzipped
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
     - Metadata column holding the sample group; one network is built per group
   * - ``--groups``
     - No
     - str
     - all
     - both
     - Comma-separated group values to keep
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
     - Prefix of every output file
   * - ``--sep``
     - No
     - str
     - ``,`` for .csv, tab otherwise
     - both
     - Field separator of both tables
   * - ``--covariates``
     - No
     - str
     - \ 
     - both
     - Comma-separated metadata columns (numeric or categorical) regressed out of every feature, per group
   * - ``--seed``
     - No
     - int
     - 20260731 / 0
     - both
     - Random seed (permutations / StARS subsamples)
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
     - ``auto``, ``counts`` or ``log2p1`` (UCSC Xena STAR counts are log2(count+1))
   * - ``--tcga``
     - No
     - bool
     - False
     - transcriptomics
     - Groups from TCGA barcodes (01 → tumor, 11 → normal), one aliquot per patient; ``-m`` not needed
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
     - Significance of the expression-bias test that stops the gate
   * - ``--gate-top``
     - No
     - int
     - 100
     - transcriptomics
     - Strongest edges inspected by the gate (lower it for small panels)
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
     - False discovery rate of the edges
   * - ``--n-perm``
     - No
     - int
     - 3
     - transcriptomics
     - Permutations of the null distribution
   * - ``--prevalence``
     - No
     - str
     - auto
     - metagenomics
     - Prevalence threshold of the taxon panel, or ``auto``
   * - ``--stars-beta``
     - No
     - float
     - 0.10
     - metagenomics
     - StARS instability bound
   * - ``--n-sub``
     - No
     - int
     - 50
     - metagenomics
     - StARS subsamples

.. [1] Not needed for ``transcriptomics --tcga``, where groups come from the barcodes.

What is data-driven
-------------------

The pipelines are not parameter-free. Each value in the report is labelled
with where it came from:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Value
     - Kind
     - How it is chosen
   * - Input scale
     - data-driven
     - integers → counts; non-integers ≤ 50 → log2(count + 1)
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
     - lowest threshold (5 % grid) leaving fewer taxa than samples in the smallest group
   * - Graphical lasso penalty
     - data-driven
     - StARS, largest stable network under the instability bound
   * - FDR, permutations, StARS bound, seeds
     - default
     - conventional values, overridable by flag

Output
------

For every group ``<g>`` (lower-cased, non-alphanumerics replaced by ``_``):

``<prefix>_<g>.tsv``
   Edge list with header ``N1 N2 Weight``. **Weight is a distance**,
   ``1 − |r|``: Pyntacle uses edge weights as shortest-path lengths, so a
   strong association must be a short edge. Read it with ``-t edgelist -w``.
   Nodes without edges are not written.

``<prefix>_<g>.graphml``
   The same edges with ``assoc_weight`` (signed partial correlation), ``abs_r``,
   ``pyntacle_weight`` and, for transcriptomics, ``q_value``; node attributes
   ``mean_log2_expr``, ``symbol``, ``biotype`` (transcriptomics) or
   ``mean_rel_abundance``, ``prevalence`` (metagenomics).

``<prefix>_report.tsv`` and ``<prefix>_report.json``
   Every value used, with its kind (data-driven / default / user), the
   diagnostics behind the data-driven choices (gate table, StARS instability
   curve, prevalence grid, size factors), warnings, and package versions.

With ``--save-stages``: ``<prefix>_<g>_<stage>.tsv.gz`` intermediate matrices.

Examples
--------

A generic dataset, then key players on the tumour network:

.. code-block:: console

   python3 main.py omics metagenomics -i relabund.tsv -m samples.tsv \
       --group-col condition -o nets/
   python3 main.py keyplayer kp-finder -t edgelist -w -i nets/relabund_tumor.tsv \
       -k 2 -oper all -a greedy -o kp/

Adjusting for covariates (age and a categorical batch):

.. code-block:: console

   python3 main.py omics transcriptomics -i counts.tsv -m samples.tsv \
       --group-col condition --covariates age,batch -o nets/

The colorectal cancer case study (TCGA-COAD from UCSC Xena; TCMA microbiome):

.. code-block:: console

   # transcriptome: 1,715 nodes / 3,148 edges (tumour), 824 / 3,371 (normal)
   python3 main.py omics transcriptomics -i TCGA-COAD.star_counts.tsv --tcga \
       --biotype mygene_biotype_cache_hvg.csv --drop-sex-genes -o coad/ --prefix coad

   # microbiome, genus: the automatic prevalence threshold is 0.15
   python3 main.py omics metagenomics -i bacteria.sample.relabund.genus.txt \
       -m sample_metadata_genus.txt --group-col Definition \
       --groups "Primary Solid Tumor,Solid Tissue Normal" -o tcma/ --prefix genus

   # microbiome, family: same threshold as genus, applied uniformly
   python3 main.py omics metagenomics -i bacteria.sample.relabund.family.txt \
       -m sample_metadata_family.txt --group-col Definition \
       --groups "Primary Solid Tumor,Solid Tissue Normal" -o tcma/ --prefix family \
       --prevalence 0.15

.. tip::

   Analysing the same samples at several taxonomic ranks? Let the automatic
   rule choose the threshold on one rank and pass it with ``--prevalence`` to
   the others, so every rank uses the same panel rule.
