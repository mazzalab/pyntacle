"""Compositional data: closure, zero replacement, centred log-ratio
(Aitchison 1982; Martin-Fernandez et al. 2003). Same formulas as
scikit-bio's closure / multi_replace / clr, without the dependency."""
import numpy as np
import pandas as pd


def closure(a):
    a = np.asarray(a, dtype=float)
    return a / a.sum(axis=1, keepdims=True)


def multiplicative_replacement(a, delta=None):
    a = closure(a)
    d = (1.0 / a.shape[1]) ** 2 if delta is None else delta
    zeros = a == 0
    k = zeros.sum(axis=1, keepdims=True)
    return closure(np.where(zeros, d, a * (1.0 - k * d)))


def clr(a):
    la = np.log(a)
    return la - la.mean(axis=1, keepdims=True)


def drop_allzero(df):
    zero = df.sum(axis=1) == 0
    return df.loc[~zero], list(df.index[zero])


def coda_transform(df):
    return pd.DataFrame(clr(multiplicative_replacement(closure(df.values))),
                        index=df.index, columns=df.columns)
