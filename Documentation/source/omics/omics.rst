Omics to networks
=================

The ``omics`` command (:doc:`../cli/omics/index`) builds association networks
from raw omics data: one network per sample group (for example tumour and
normal tissue), ready for every other Pyntacle analysis. This page describes
what each pipeline does and why, with the reference behind each step.

Both pipelines estimate **partial correlations**: the association between two
features once all the other features are accounted for. An edge therefore
stands for a direct dependence, not for one mediated by a third feature. The
two pipelines differ in how they prepare the raw data for that estimate.

.. contents::
   :local:
   :depth: 2

Transcriptomics
---------------

Input scale
~~~~~~~~~~~

The pipeline expects raw counts. Public releases often use another scale:
the UCSC Xena GDC hub (`Goldman et al. 2020`_), for example, distributes STAR
gene counts as ``log2(count + 1)``. Library-size normalisation applied to log
values gives wrong results without any error, so the scale is detected and
log values are transformed back:

* integer values are counts;
* non-integer values no larger than 50 are ``log2(count + 1)``, provided that
  2\ :sup:`x` − 1 gives integers back;
* everything else is refused: negative values (z-scores, log-ratios),
  non-integer values above 50 (TPM, FPKM) and log values that do not come
  back to integers (``log2(TPM + 1)``, ``log2(FPKM + 1)``).

``--input-scale`` overrides the detection, for example for the non-integer
expected counts of RSEM.

With ``--tcga``, the sample groups come from the TCGA barcodes instead of a
metadata table. The sample type code in the fourth field of the barcode
selects the group: by default 01 (primary solid tumour) is ``tumor`` and 11
(solid tissue normal) is ``normal``, and every other type is left out and
counted in the report. ``--tcga-types`` selects other codes, for example
06 (metastatic) for melanoma or 03 (primary blood-derived cancer) for
leukaemia. When a patient has several samples of the same type, one is kept,
from vial A if there is one.

Normalisation
~~~~~~~~~~~~~

Counts are normalised by median-of-ratios size factors (`Anders & Huber
2010`_; `Love et al. 2014`_) and transformed to ``log2(x + 1)``. Size factors
are estimated on all groups together, so every group is on the same scale.
Zeros are handled as in the case study: a gene's reference is the geometric
mean of its non-zero counts, and each sample's median skips the genes it does
not detect. DESeq2's default instead uses only the genes detected in every
sample, which in large cohorts can leave few genes.

Gene selection
~~~~~~~~~~~~~~

Genes are selected in each group separately, with two Gaussian mixture
models of two components each (`McLachlan & Peel 2000`_), so that no
expression or variance threshold is set by hand:

1. a mixture on mean expression separates expressed from silent genes;
2. a LOESS regression (`Cleveland 1979`_) of log variance on mean expression
   gives the variance expected at each expression level; a mixture on the
   residuals keeps the genes more variable than expected.

For each group the report gives the Spearman correlation between residual
and mean expression. A value close to 0 shows that the selection is not
driven by expression level. The genes selected in any group form a single
panel, shared by all groups.

Two filters are optional. ``--biotype`` keeps protein-coding and non-coding
RNA genes, using the MyGene.info annotation (`Wu et al. 2013`_; `Xin et al.
2016`_) queried online or read from a file. ``--drop-sex-genes`` removes 16
sex-linked genes (XIST, RPS4Y1, DDX3Y, …), which drive co-expression in
cohorts of mixed sex without any biological link to the condition studied.

Expression gate
~~~~~~~~~~~~~~~

Weakly expressed genes have frequent zero counts, and zeros shared by two
genes produce strong but spurious partial correlations. The gate removes the
genes below a mean-expression quantile, raising the quantile in steps of 0.05.
It stops at the first quantile at which the genes of the strongest edges
(100 by default) are no longer less expressed than the other genes, by a
one-sided Mann–Whitney U test (`Mann & Whitney 1947`_). If the panel would
fall below ``--gate-min-genes`` genes first, the command stops with an error
rather than build a biased network. The whole search is written to the
report.

Partial correlations and edge calling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With thousands of genes and hundreds of samples, the sample covariance
matrix cannot be inverted reliably. It is shrunk towards a scaled identity
with the analytical Ledoit–Wolf intensity (`Ledoit & Wolf 2004`_), following
the shrinkage approach to gene association networks (`Schäfer & Strimmer
2005`_), and then inverted to partial correlations. Covariates given with
``--covariates`` are regressed out of every gene first.

Edges are called against a permutation null: each gene is shuffled across
samples independently of the others, which destroys every association but
keeps each gene's distribution (`Tusher et al. 2001`_). On the permuted data
the shrinkage intensity is held at its observed value; estimating it again
there would inflate it, narrow the null and understate the error rate. The
false discovery rate of the top-ranked edges is estimated from how often the
null exceeds them (`Storey & Tibshirani 2003`_), and edges are kept down to
the requested FDR (0.001 by default).

The null is independence of all genes, so the FDR bounds the edges between
genes that are not associated at all. Shrinkage also mixes part of the
marginal correlation into the partial correlation, so two genes that share a
neighbour can pass the threshold without a direct link. In simulations with a
known sparse network this mattered only under strong shrinkage (intensity of
0.5 or more, weak associations for the number of samples): such indirect
edges then took the realised FDR above the nominal one. With the lower
shrinkage of strongly associated data, the realised FDR stayed at or below
the nominal level. The report gives the intensity of each group.

Metagenomics
------------

Microbiome profiles, whether relative abundances such as those of The Cancer
Microbiome Atlas (`Dohlman et al. 2021`_) or read counts, are compositional:
each sample carries only the proportions of its taxa, so correlations
computed directly on them can be spurious (`Aitchison 1982`_; `Lovell et al.
2015`_; `Gloor et al. 2017`_).

Taxonomic rank
~~~~~~~~~~~~~~

Profilers such as MetaPhlAn (`Blanco-Míguez et al. 2023`_) list every rank in
one table, from kingdom to strain, and each rank sums the ranks below it. A
network mixing ranks would link every genus to its own family, so a single
rank is analysed: the one chosen with ``--rank``, or the only one present, as
in a table collapsed to one level with QIIME 2 (`Bolyen et al. 2019`_).

Taxon panel
~~~~~~~~~~~

A taxon is kept if it is present in at least a given fraction of the samples
of **any** group, so that all groups share one panel and their networks can be
compared. The automatic threshold is the lowest on a grid from 0.05 to 0.50
in steps of 0.05 that leaves fewer taxa than there are samples in the
smallest group, the limit beyond which a covariance-based estimator has more
parameters than observations. When several taxonomic ranks are analysed,
choose the threshold on one rank and pass it to the others with
``--prevalence``.

Compositional transform
~~~~~~~~~~~~~~~~~~~~~~~

In each group:

1. samples with no reads in the panel are dropped (and named in the report);
2. the panel is rescaled to sum to one in every sample, since selecting taxa
   breaks the original closure;
3. zeros are replaced by multiplicative simple replacement
   (`Martín-Fernández et al. 2003`_) rather than by an additive pseudocount,
   which distorts the ratios between the other taxa (`Gloor et al. 2017`_);
4. the values are transformed to centred log-ratio coordinates
   (`Aitchison 1982`_).

Covariates given with ``--covariates`` are then regressed out of the
coordinates.

Network inference
~~~~~~~~~~~~~~~~~

The network is the graphical lasso estimate of the precision matrix
(`Friedman et al. 2008`_). Its penalty is chosen by the Stability Approach to
Regularization Selection (StARS; `Liu et al. 2010`_): the lasso is refitted
on random subsamples along a path of penalties, and the chosen penalty gives
the densest network whose edge instability stays below a bound. The bound, β,
trades precision for recall: a lower bound selects a sparser network whose
edges recur across subsamples, a higher bound keeps more edges, false ones
included. Pyntacle uses 0.10, the default of the huge package
(`Zhao et al. 2012`_), with which the networks of the case study were built;
`Liu et al. 2010`_ and the SpiecEasi package use 0.05, which
``--stars-beta 0.05`` selects. Together, the transform and the estimator are the SPIEC-EASI
method (`Kurtz et al. 2015`_). For a given seed the result is deterministic.

Sparse profiles limit what the network can say. After zero replacement, the
CLR coordinate of a taxon absent from a sample depends only on the sample's
geometric mean, so taxa absent from the same samples look associated
(`Austin & Korem 2025`_). When most values are zeros, an edge mostly records
that two taxa are present or absent together, not that their abundances
covary; the fraction of zeros in the panel of each group is in the report.

Weights and distances
---------------------

The edge list written by ``omics`` carries the signed partial correlation
*r*, the quantity the pipeline estimates. Pyntacle reads it with
``-w --weight-type signed`` (:doc:`/weights`): the networks are analysed as
unsigned weighted networks, with the magnitude \|r\| as the strength of the
tie and the sign kept as an edge attribute, as in unsigned weighted
co-expression networks (`Zhang & Horvath 2005`_).

Shortest-path measures (closeness, radiality, key-player dF and m-reach,
group closeness) need lengths, and a negative weight cannot be one: on an
undirected network, a negative edge makes every path through it arbitrarily
short. Strengths are therefore turned into lengths by their inverse,
*d* = 1/\|r\|, the usual convention for weighted shortest paths (`Newman
2001`_; `Brandes 2001`_; `Opsahl et al. 2010`_; `Rubinov & Sporns 2010`_), so
that strongly associated features lie close together. Since \|r\| ≤ 1, every
length is at least 1 and the distance-based indices stay within [0, 1]. The
transform is a convention: ``--distance-transform one-minus`` (1 − \|r\|)
and ``neglog`` (−ln \|r\|) check that a conclusion does not depend on it.

Reproducibility
---------------

The command writes a report listing every value it used and who chose it:
the data (``data-driven``), a convention (``default``) or the user
(``user``). The report also holds the diagnostics behind each data-driven
choice and the versions of the packages used.

On the colorectal cancer case study, ``omics`` rebuilds the published
networks from the raw files. The transcriptome networks are identical edge
for edge (1,715 nodes and 3,148 edges in tumour, 824 nodes and 3,371 edges in
normal tissue). The microbiome networks have the same edges and penalties
(31 and 21 edges at genus rank, 29 and 17 at family rank), and their partial
correlations match to 5 × 10\ :sup:`−7` with scikit-learn 1.8; earlier
releases of its graphical lasso solver reach the same networks with values
that differ in the third decimal.

References
----------

* `Aitchison 1982`_ — The statistical analysis of compositional data. *J R Stat Soc B* 44:139–177.
* `Anders & Huber 2010`_ — Differential expression analysis for sequence count data. *Genome Biol* 11:R106.
* `Austin & Korem 2025`_ — Compositional transformations can reasonably introduce phenotype-associated values into sparse features. *mSystems* 10:e0002125.
* `Blanco-Míguez et al. 2023`_ — Extending and improving metagenomic taxonomic profiling with uncharacterized species using MetaPhlAn 4. *Nat Biotechnol* 41:1633–1644.
* `Bolyen et al. 2019`_ — Reproducible, interactive, scalable and extensible microbiome data science using QIIME 2. *Nat Biotechnol* 37:852–857.
* `Brandes 2001`_ — A faster algorithm for betweenness centrality. *J Math Sociol* 25:163–177.
* `Cleveland 1979`_ — Robust locally weighted regression and smoothing scatterplots. *J Am Stat Assoc* 74:829–836.
* `Dohlman et al. 2021`_ — The cancer microbiome atlas. *Cell Host Microbe* 29:281–298.
* `Friedman et al. 2008`_ — Sparse inverse covariance estimation with the graphical lasso. *Biostatistics* 9:432–441.
* `Gloor et al. 2017`_ — Microbiome datasets are compositional: and this is not optional. *Front Microbiol* 8:2224.
* `Goldman et al. 2020`_ — Visualizing and interpreting cancer genomics data via the Xena platform. *Nat Biotechnol* 38:675–678.
* `Kurtz et al. 2015`_ — Sparse and compositionally robust inference of microbial ecological networks. *PLoS Comput Biol* 11:e1004226.
* `Ledoit & Wolf 2004`_ — A well-conditioned estimator for large-dimensional covariance matrices. *J Multivar Anal* 88:365–411.
* `Liu et al. 2010`_ — Stability approach to regularization selection (StARS) for high dimensional graphical models. *Adv Neural Inf Process Syst* 24:1432–1440.
* `Love et al. 2014`_ — Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biol* 15:550.
* `Lovell et al. 2015`_ — Proportionality: a valid alternative to correlation for relative data. *PLoS Comput Biol* 11:e1004075.
* `Mann & Whitney 1947`_ — On a test of whether one of two random variables is stochastically larger than the other. *Ann Math Stat* 18:50–60.
* `Martín-Fernández et al. 2003`_ — Dealing with zeros and missing values in compositional data sets using nonparametric imputation. *Math Geol* 35:253–278.
* `McLachlan & Peel 2000`_ — *Finite Mixture Models*. Wiley.
* `Newman 2001`_ — Scientific collaboration networks. II. Shortest paths, weighted networks, and centrality. *Phys Rev E* 64:016132.
* `Opsahl et al. 2010`_ — Node centrality in weighted networks: generalizing degree and shortest paths. *Soc Networks* 32:245–251.
* `Rubinov & Sporns 2010`_ — Complex network measures of brain connectivity: uses and interpretations. *NeuroImage* 52:1059–1069.
* `Schäfer & Strimmer 2005`_ — A shrinkage approach to large-scale covariance matrix estimation and implications for functional genomics. *Stat Appl Genet Mol Biol* 4:32.
* `Storey & Tibshirani 2003`_ — Statistical significance for genomewide studies. *PNAS* 100:9440–9445.
* `Tusher et al. 2001`_ — Significance analysis of microarrays applied to the ionizing radiation response. *PNAS* 98:5116–5121.
* `Wu et al. 2013`_ — BioGPS and MyGene.info: organizing online, gene-centric information. *Nucleic Acids Res* 41:D561–D565.
* `Xin et al. 2016`_ — High-performance web services for querying gene and variant annotation. *Genome Biol* 17:91.
* `Zhang & Horvath 2005`_ — A general framework for weighted gene co-expression network analysis. *Stat Appl Genet Mol Biol* 4:17.
* `Zhao et al. 2012`_ — The huge package for high-dimensional undirected graph estimation in R. *J Mach Learn Res* 13:1059–1062.

.. _`Aitchison 1982`: https://doi.org/10.1111/j.2517-6161.1982.tb01195.x
.. _`Austin & Korem 2025`: https://doi.org/10.1128/msystems.00021-25
.. _`Anders & Huber 2010`: https://doi.org/10.1186/gb-2010-11-10-r106
.. _`Cleveland 1979`: https://doi.org/10.1080/01621459.1979.10481038
.. _`Dohlman et al. 2021`: https://doi.org/10.1016/j.chom.2020.12.001
.. _`Friedman et al. 2008`: https://doi.org/10.1093/biostatistics/kxm045
.. _`Gloor et al. 2017`: https://doi.org/10.3389/fmicb.2017.02224
.. _`Goldman et al. 2020`: https://doi.org/10.1038/s41587-020-0546-8
.. _`Kurtz et al. 2015`: https://doi.org/10.1371/journal.pcbi.1004226
.. _`Ledoit & Wolf 2004`: https://doi.org/10.1016/S0047-259X(03)00096-4
.. _`Liu et al. 2010`: https://pubmed.ncbi.nlm.nih.gov/25152607/
.. _`Love et al. 2014`: https://doi.org/10.1186/s13059-014-0550-8
.. _`Lovell et al. 2015`: https://doi.org/10.1371/journal.pcbi.1004075
.. _`Mann & Whitney 1947`: https://doi.org/10.1214/aoms/1177730491
.. _`Martín-Fernández et al. 2003`: https://doi.org/10.1023/A:1023866030544
.. _`McLachlan & Peel 2000`: https://doi.org/10.1002/0471721182
.. _`Schäfer & Strimmer 2005`: https://doi.org/10.2202/1544-6115.1175
.. _`Storey & Tibshirani 2003`: https://doi.org/10.1073/pnas.1530509100
.. _`Tusher et al. 2001`: https://doi.org/10.1073/pnas.091062498
.. _`Wu et al. 2013`: https://doi.org/10.1093/nar/gks1114
.. _`Xin et al. 2016`: https://doi.org/10.1186/s13059-016-0953-9
.. _`Zhao et al. 2012`: https://pubmed.ncbi.nlm.nih.gov/26834510/
.. _`Blanco-Míguez et al. 2023`: https://doi.org/10.1038/s41587-023-01688-w
.. _`Bolyen et al. 2019`: https://doi.org/10.1038/s41587-019-0209-9
.. _`Brandes 2001`: https://doi.org/10.1080/0022250X.2001.9990249
.. _`Newman 2001`: https://doi.org/10.1103/PhysRevE.64.016132
.. _`Opsahl et al. 2010`: https://doi.org/10.1016/j.socnet.2010.03.006
.. _`Rubinov & Sporns 2010`: https://doi.org/10.1016/j.neuroimage.2009.10.003
.. _`Zhang & Horvath 2005`: https://doi.org/10.2202/1544-6115.1128
