Omics to networks
=================

The ``omics`` command (:doc:`../cli/omics/index`) builds association networks
from raw omics data: one network per sample group (for example tumour and
normal tissue), ready for every other Pyntacle analysis. This page describes
what each pipeline does and why, with the references behind every step.

Both pipelines estimate **partial correlations** — the association between
two features after accounting for all the others — so an edge means a direct
dependence, not one mediated by a third feature. They differ in how the raw
data are made fit for that estimate.

.. contents::
   :local:
   :depth: 2

Transcriptomics
---------------

Input scale
~~~~~~~~~~~

Raw counts are expected. Public releases often ship another scale: the UCSC
Xena GDC hub (`Goldman et al. 2020`_) distributes STAR gene counts as
``log2(count + 1)``. The scale is detected (integers are counts; non-integers
no larger than 50 are ``log2(count + 1)``) and back-transformed, because
library-size normalisation applied to log values is silently wrong.
Normalised values (TPM, FPKM, z-scores) are refused.

With ``--tcga``, sample groups come from the TCGA barcode (sample type 01 →
tumour, 11 → normal) and one aliquot is kept per patient, preferring vial A.

Normalisation
~~~~~~~~~~~~~

Counts are normalised by the DESeq2 median-of-ratios method (`Anders & Huber
2010`_; `Love et al. 2014`_) and transformed to ``log2(x + 1)``. Size factors
are estimated on all groups together, so every group is on the same scale.

Gene selection
~~~~~~~~~~~~~~

Genes are selected separately in each group by two two-component Gaussian
mixture models (`McLachlan & Peel 2000`_), so no expression or variance
threshold is set by hand:

1. a mixture on mean expression separates expressed from silent genes;
2. a LOESS regression (`Cleveland 1979`_) of log variance on mean expression
   gives the variance expected at each expression level; a mixture on the
   residuals keeps the genes more variable than expected.

The report gives, for each group, the Spearman correlation between residual
and mean expression: it should be close to 0, showing that selection is not
driven by expression level. The union of the groups' selections forms a
single gene panel.

Optional filters: ``--biotype`` keeps protein-coding and non-coding RNA genes
using MyGene.info annotation (`Wu et al. 2013`_; `Xin et al. 2016`_), either
queried online or read from a file; ``--drop-sex-genes`` removes 16
sex-linked genes (XIST, RPS4Y1, DDX3Y, …), a known technical confounder of
co-expression in cohorts of mixed sex.

Expression gate
~~~~~~~~~~~~~~~

Weakly expressed genes have frequent zero counts, and zeros shared by two
genes produce strong but spurious partial correlations. The gate raises a
mean-expression quantile in steps of 0.05 and stops at the first quantile at
which the genes involved in the strongest edges (default 100) are no longer
less expressed than the others, by a one-sided Mann–Whitney U test (`Mann &
Whitney 1947`_). The whole search is written to the report.

Partial correlations and edge calling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With thousands of genes and hundreds of samples the sample covariance matrix
cannot be inverted reliably. It is shrunk towards a scaled identity with the
analytical Ledoit–Wolf intensity (`Ledoit & Wolf 2004`_), following the
shrinkage approach to gene association networks (`Schäfer & Strimmer 2005`_),
then inverted to partial correlations. Optional covariates are regressed out
of every gene first.

Edges are called against a permutation null: each gene is shuffled
independently across samples, which destroys every association while
keeping each gene's distribution (`Tusher et al. 2001`_). The shrinkage
intensity is held at its observed value on permuted data — re-estimating it
there would inflate it, narrow the null and make the error rate optimistic.
The false discovery rate of the top-ranked edges is estimated from the null
exceedances (`Storey & Tibshirani 2003`_) and edges are kept up to the
requested FDR (default 0.001).

Metagenomics
------------

Relative abundances such as those of The Cancer Microbiome Atlas (`Dohlman et
al. 2021`_) are compositional: they sum to one, so correlations computed
directly on them can be spurious (`Aitchison 1982`_; `Lovell et al. 2015`_;
`Gloor et al. 2017`_).

Taxon panel
~~~~~~~~~~~

A taxon is kept if it is present in at least a given fraction of the samples
of **any** group, so that all groups share one panel and their networks are
comparable. The automatic threshold is the lowest on a 5 % grid that leaves
fewer taxa than samples in the smallest group — the limiting case for any
covariance-based estimator. When several taxonomic ranks are analysed, choose
the threshold on one rank and pass it to the others with ``--prevalence``.

Compositional transform
~~~~~~~~~~~~~~~~~~~~~~~

Per group: samples with no reads in the panel are dropped; the panel is
re-closed to unit sum (selecting taxa breaks the closure); zeros are replaced
by multiplicative simple replacement (`Martín-Fernández et al. 2003`_) rather
than an additive pseudocount, which is not compositionally coherent (`Gloor et
al. 2017`_); the result is transformed to centred log-ratio coordinates
(`Aitchison 1982`_). Optional covariates are regressed out of the coordinates.

Network inference
~~~~~~~~~~~~~~~~~

The network is the graphical lasso estimate of the precision matrix (`Friedman
et al. 2008`_). Its penalty is chosen by the Stability Approach to
Regularization Selection (StARS; `Liu et al. 2010`_): the lasso is refitted on
subsamples along a path of penalties and the chosen penalty gives the densest
network whose edge instability stays below a bound. The bound defaults to
0.10, the default of the huge package (`Zhao et al. 2012`_), rather than the
0.05 of the original description, which can leave the network empty at small
sample sizes. Transform and estimator together are the SPIEC-EASI method
(`Kurtz et al. 2015`_). The fit is deterministic for a given seed.

Weights and distances
---------------------

The edge list written by ``omics`` carries the signed partial correlation
*r*, the quantity the pipeline estimates. Pyntacle reads it with
``-w --weight-type signed`` (:doc:`/weights`): the networks are analysed as
unsigned weighted networks, with the magnitude \|r\| as the strength of the
tie and the sign kept as an edge attribute — the convention of unsigned
weighted co-expression networks (`Zhang & Horvath 2005`_).

Shortest-path measures (closeness, radiality, key-player dF and m-reach,
group closeness) need lengths, and a negative weight cannot be one: on an
undirected network it makes every path through it arbitrarily short. Strengths
are turned into lengths by their inverse, *d* = 1/\|r\|, the usual convention
for weighted shortest paths (`Newman 2001`_; `Brandes 2001`_; `Opsahl et al.
2010`_; `Rubinov & Sporns 2010`_), so that strongly associated features lie
close together. Since \|r\| ≤ 1, every length is at least 1 and the
distance-based indices stay within [0, 1]. The transform is a convention:
``--distance-transform one-minus`` (1 − \|r\|) and ``neglog`` (−ln \|r\|)
allow checking that a conclusion does not depend on it.

Reproducibility
---------------

The command writes a report listing every value it used and whether the data
(``data-driven``), a convention (``default``) or the user (``user``) chose it,
with the diagnostics behind each data-driven choice and the package versions.

On the colorectal cancer case study, ``omics`` reproduces the published
networks from the raw files: the transcriptome networks edge for edge
(1,715 nodes and 3,148 edges in tumour, 824 and 3,371 in normal tissue), and
the microbiome networks with the same edges and penalties (31 and 21 edges at
genus rank, 29 and 17 at family rank). Partial correlations of the microbiome
networks match to 5 × 10\ :sup:`−7` with scikit-learn 1.8; earlier releases
of its graphical lasso solver converge to the same networks with values that
differ in the third decimal.

References
----------

* `Aitchison 1982`_ — The statistical analysis of compositional data. *J R Stat Soc B* 44:139–177.
* `Anders & Huber 2010`_ — Differential expression analysis for sequence count data. *Genome Biol* 11:R106.
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
.. _`Brandes 2001`: https://doi.org/10.1080/0022250X.2001.9990249
.. _`Newman 2001`: https://doi.org/10.1103/PhysRevE.64.016132
.. _`Opsahl et al. 2010`: https://doi.org/10.1016/j.socnet.2010.03.006
.. _`Rubinov & Sporns 2010`: https://doi.org/10.1016/j.neuroimage.2009.10.003
.. _`Zhang & Horvath 2005`: https://doi.org/10.2202/1544-6115.1128
