#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def clean_help(s: Optional[str]) -> str:
    if not s or s is argparse.SUPPRESS:
        return ""
    s = strip_ansi(str(s))
    # remove your tags
    s = re.sub(r"^\s*-\[(optional|required)\]\s*", "", s, flags=re.IGNORECASE)
    # remove leading bullets/dots that leak into docs
    s = re.sub(r"^\s*[•·\-–]+\s*", "", s)
    # collapse internal newlines/spaces (table cells hate raw newlines)
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def action_type(a: argparse.Action) -> str:
    # store_true/false
    if isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return "bool"
    if getattr(a, "type", None) is not None:
        try:
            return a.type.__name__
        except Exception:
            return str(a.type)
    # infer from choices if possible
    if a.choices:
        tset = {type(x) for x in a.choices if x is not None}
        if len(tset) == 1:
            return next(iter(tset)).__name__
    return "str"

def required_flag(a: argparse.Action) -> str:
    # optional arguments
    if a.option_strings:
        return "Yes" if getattr(a, "required", False) else "No"
    # positional: required unless nargs makes it optional
    nargs = getattr(a, "nargs", None)
    if nargs in ("?", "*"):
        return "No"
    return "Yes"

def default_value(a: argparse.Action) -> str:
    d = getattr(a, "default", None)
    if d is None or d is argparse.SUPPRESS:
        return ""
    # argparse uses '==SUPPRESS' sometimes; already handled
    return strip_ansi(str(d))

def choices_value(a: argparse.Action) -> str:
    ch = getattr(a, "choices", None)
    if not ch:
        return ""
    # keep readable
    return ", ".join(strip_ansi(str(x)) for x in ch)

def option_label(a: argparse.Action) -> str:
    if a.option_strings:
        return ", ".join(a.option_strings)
    return a.metavar or a.dest

def iter_actions(p: argparse.ArgumentParser) -> List[argparse.Action]:
    out: List[argparse.Action] = []
    for a in p._actions:
        # skip help
        if isinstance(a, argparse._HelpAction):
            continue
        out.append(a)
    return out

def get_subparsers_action(p: argparse.ArgumentParser) -> Optional[argparse._SubParsersAction]:
    for a in p._actions:
        if isinstance(a, argparse._SubParsersAction):
            return a
    return None

def clean_usage(p: argparse.ArgumentParser) -> str:
    # prefer format_usage (includes "usage:"), but we strip that prefix
    u = strip_ansi(p.format_usage())
    u = u.replace("\r", "").strip("\n")
    u = re.sub(r"^\s*usage:\s*", "", u, flags=re.IGNORECASE).strip()
    # parser.py often prefixes a newline in usage=...
    u = u.strip()
    return u

def write_list_table(rows: List[Tuple[str, str, str, str, str, str]]) -> str:
    # rows are already clean single-line strings
    lines = []
    lines.append(".. list-table::")
    lines.append("   :header-rows: 1")
    lines.append("   :widths: 18 8 10 10 12 42")
    lines.append("")
    lines.append("   * - Option")
    lines.append("     - Required")
    lines.append("     - Type")
    lines.append("     - Default")
    lines.append("     - Choices")
    lines.append("     - Help")
    for r in rows:
        lines.append(f"   * - {r[0]}")
        lines.append(f"     - {r[1]}")
        lines.append(f"     - {r[2]}")
        lines.append(f"     - {r[3]}")
        lines.append(f"     - {r[4]}")
        lines.append(f"     - {r[5]}")
    lines.append("")
    return "\n".join(lines)

def main() -> int:
    # IMPORTANT: force no ANSI in docs
    os.environ["PYNTACLE_DOCS"] = "1"

    # add repo root to path so `import pyntacle` works
    here = Path(__file__).resolve()
    repo_root = here.parents[4]  # .../Documentation/source/_scripts -> repo root
    sys.path.insert(0, str(repo_root))

    from pyntacle import parser as pynt_parser  # type: ignore

    top = pynt_parser.create_parser()
    sub = get_subparsers_action(top)
    if sub is None:
        raise RuntimeError("No subparsers found in the main parser (argparse._SubParsersAction).")

    # output dirs
    source_dir = repo_root / "Documentation" / "source"
    cli_dir = source_dir / "cli"
    cli_dir.mkdir(parents=True, exist_ok=True)

    # command order = insertion order in parser
    commands: List[Tuple[str, argparse.ArgumentParser]] = []
    for name, sp in sub.choices.items():
        commands.append((name, sp))

    # ---- write per-command pages
    for name, p in commands:
        title = f"{name}"
        fname = cli_dir / f"{name}.rst"

        # build option rows
        rows = []
        for a in iter_actions(p):
            rows.append((
                strip_ansi(option_label(a)),
                required_flag(a),
                action_type(a),
                default_value(a),
                choices_value(a),
                clean_help(getattr(a, "help", "")),
            ))

        content = []
        content.append(title)
        content.append("=" * len(title))
        content.append("")
        content.append("Synopsis")
        content.append("--------")
        content.append("")
        content.append(".. code-block:: text")
        content.append("")
        content.append(f"   {clean_usage(p)}")
        content.append("")
        content.append("Options")
        content.append("-------")
        content.append("")
        content.append(write_list_table(rows))

        fname.write_text("\n".join(content), encoding="utf-8")

    # ---- write CLI index with dropdowns (closed by default)
    idx = []
    idx.append("Command-line interface")
    idx.append("======================")
    idx.append("")
    idx.append("This section documents the Pyntacle CLI commands and their options.")
    idx.append("")
    idx.append("Contents")
    idx.append("--------")
    idx.append("")
    idx.append(".. raw:: html")
    idx.append("")
    idx.append("   <div class=\"cli-index\">")
    idx.append("")

    for name, p in commands:
        # short help = subparser description if available, otherwise blank
        short = strip_ansi(getattr(p, "description", "") or "").strip()
        short = re.sub(r"\s*\n\s*", " ", short).strip()
        if short:
            short = clean_help(short)
        idx.append(".. raw:: html")
        idx.append("")
        idx.append(f"   <details class=\"cli-details\">")
        idx.append(f"     <summary><span class=\"cli-cmd\">{name}</span></summary>")
        idx.append(f"     <div class=\"cli-inner\">")
        idx.append("")
        if short:
            idx.append(f"{short}")
            idx.append("")
        idx.append(f":doc:`Open {name} documentation <{name}>`")
        idx.append("")
        idx.append(".. raw:: html")
        idx.append("")
        idx.append("     </div>")
        idx.append("   </details>")
        idx.append("")

    idx.append(".. raw:: html")
    idx.append("")
    idx.append("   </div>")
    idx.append("")
    # hidden toctree so Sphinx actually includes pages
    idx.append(".. toctree::")
    idx.append("   :maxdepth: 1")
    idx.append("   :hidden:")
    idx.append("")
    for name, _ in commands:
        idx.append(f"   {name}")
    idx.append("")

    (cli_dir / "index.rst").write_text("\n".join(idx), encoding="utf-8")

    print(f"[OK] Generated CLI docs in: {cli_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
