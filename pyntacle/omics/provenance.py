"""Every value a pipeline uses, with where it came from.

The report separates what the data decided (data-driven), what a convention
decided (default) and what the user decided (user), so the Methods text can
say which is which.
"""
import csv
import datetime
import json
import os
import platform

KINDS = ("data-driven", "default", "user")


def _plain(obj):
    if hasattr(obj, "to_dict") and hasattr(obj, "columns"):
        return obj.to_dict(orient="records")
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    return obj


class Provenance:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.values, self.diagnostics, self.warnings = [], {}, []

    def record(self, step, name, value, kind, note=""):
        if kind not in KINDS:
            raise ValueError("kind must be one of {}, got {!r}".format(KINDS, kind))
        self.values.append({"step": step, "name": name, "value": _plain(value),
                            "kind": kind, "note": note})

    def diagnostic(self, name, obj):
        self.diagnostics[name] = _plain(obj)

    def warn(self, msg):
        self.warnings.append(msg)

    def to_dict(self):
        import numpy
        import pandas
        import scipy
        import sklearn
        import statsmodels
        return {"pipeline": self.pipeline,
                "date": datetime.datetime.now().isoformat(timespec="seconds"),
                "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                             "pandas": pandas.__version__, "scipy": scipy.__version__,
                             "scikit-learn": sklearn.__version__,
                             "statsmodels": statsmodels.__version__},
                "values": self.values, "diagnostics": self.diagnostics,
                "warnings": self.warnings}

    def write(self, outdir, prefix):
        with open(os.path.join(outdir, prefix + "_report.json"), "w") as fh:
            json.dump(self.to_dict(), fh, indent=1, default=str)
        with open(os.path.join(outdir, prefix + "_report.tsv"), "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["step", "name", "value", "kind", "note"])
            for v in self.values:
                w.writerow([v["step"], v["name"], v["value"], v["kind"], v["note"]])
