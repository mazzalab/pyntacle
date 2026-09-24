"""Raw omics matrices -> Pyntacle-ready networks (`pyntacle omics`).

Optional part of Pyntacle: it needs scikit-learn and statsmodels, which the
core does not. Importing this package never fails; `require()` does, with the
install command, before any pipeline runs.
"""
import importlib.util

# module name -> pip name
_REQUIRED = {"sklearn": "scikit-learn", "statsmodels": "statsmodels"}


def missing_dependencies():
    return [pip for mod, pip in _REQUIRED.items() if importlib.util.find_spec(mod) is None]


def require():
    missing = missing_dependencies()
    if missing:
        raise SystemExit("ERROR: 'pyntacle omics' needs " + ", ".join(missing)
                         + ". Install with: pip install " + " ".join(missing))
