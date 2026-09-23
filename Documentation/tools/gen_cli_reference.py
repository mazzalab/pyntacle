#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import argparse
import re
from pathlib import Path
import textwrap


def _find_subparsers_action(p: argparse.ArgumentParser):
    for a in p._actions:
        if isinstance(a, argparse._SubParsersAction):
            return a
    return None


def _is_hidden_action(a: argparse.Action) -> bool:
    if isinstance(a, argparse._HelpAction):
        return True
    if isinstance(a, argparse._SubParsersAction):
        return True
    if getattr(a, "help", None) is argparse.SUPPRESS:
        return True
    return False


def _opt_label(a: argparse.Action) -> str:
    if a.option_strings:
        return ", ".join(f"``{s}``" for s in a.option_strings)
    return f"``{a.dest}``"


def _type_label(a: argparse.Action) -> str:
    if isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return "flag"
    t = getattr(a, "type", None)
    if t is None:
        return "str"
    if hasattr(t, "__name__"):
        return t.__name__
    return str(t)


def _default_label(a: argparse.Action) -> str:
    d = getattr(a, "default", None)
    if d is None or d is argparse.SUPPRESS:
        return ""
    return str(d)


def _choices_label(a: argparse.Action) -> str:
    c = getattr(a, "choices", None)
    if not c:
        return ""
    try:
        return ", ".join(str(x) for x in list(c))
    except Exception:
        return str(c)


def _required_label(a: argparse.Action) -> str:
    return "yes" if getattr(a, "required", False) else "no"


def _clean_help(s: str) -> str:
    s = textwrap.dedent(s or "").strip()
    # strip tags like [optional] / [required] (case-insensitive)
    s = re.sub(r"\[(optional|required)\]", "", s, flags=re.I)
    # normalize whitespace
    s = " ".join(s.split())
    return s



def _rst_list_table(actions: list[argparse.Action], mex_groups: list[list[argparse.Action]]) -> str:
    lines = []
    lines.append(".. list-table::")
    lines.append("   :widths: 26 8 10 12 18 42")
    lines.append("   :header-rows: 1")
    lines.append("")
    lines.append("   * - Option")
    lines.append("     - Required")
    lines.append("     - Type")
    lines.append("     - Default")
    lines.append("     - Choices")
    lines.append("     - Meaning")
    for a in actions:
        opt = _opt_label(a)
        req = _required_label(a)
        typ = _type_label(a)
        dfl = _default_label(a)
        cho = _choices_label(a)
        h   = _clean_help(a.help or "")
        lines.append(f"   * - {opt}")
        lines.append(f"     - {req}")
        lines.append(f"     - {typ}")
        lines.append(f"     - {dfl}")
        lines.append(f"     - {cho}")
        lines.append(f"     - {h}")
    lines.append("")

    if mex_groups:
        lines.append("Mutually exclusive options")
        lines.append("--------------------------")
        lines.append("")
        for g in mex_groups:
            opts = ", ".join(_opt_label(a) for a in g)
            lines.append(f"- {opts}")
        lines.append("")
    return "\n".join(lines)


def render_command_rst(cmd: str, p: argparse.ArgumentParser) -> str:
    title = f"``{cmd}``"
    underline = "=" * len(title)

    usage = (p.format_usage() or "").strip()
    usage = usage.replace("usage:", "").strip()

    desc = (p.description or "").strip()

    actions = [a for a in p._actions if not _is_hidden_action(a)]

    mex_groups = []
    for g in getattr(p, "_mutually_exclusive_groups", []):
        grp_actions = [a for a in getattr(g, "_group_actions", []) if not _is_hidden_action(a)]
        if len(grp_actions) >= 2:
            mex_groups.append(grp_actions)

    out = []
    out.append(title)
    out.append(underline)
    out.append("")
    out.append("Synopsis")
    out.append("--------")
    out.append("")
    out.append(".. code-block:: console")
    out.append("")
    out.append(f"   {usage}")
    out.append("")

    if desc:
        out.append("Description")
        out.append("-----------")
        out.append("")
        out.append(desc)
        out.append("")

    out.append("Options")
    out.append("-------")
    out.append("")
    out.append(_rst_list_table(actions, mex_groups))

    return "\n".join(out)


def main():
    repo_root = Path(__file__).resolve().parents[2]
    docs_src  = repo_root / "Documentation" / "source"
    out_dir   = docs_src / "cli" / "commands"

    out_dir.mkdir(parents=True, exist_ok=True)

    # IMPORTANT: disable ANSI in parser output
    os.environ["PYNTACLE_DOCS"] = "1"

    # make repo importable so "import pyntacle.parser" works
    sys.path.insert(0, str(repo_root))

    from pyntacle.parser import create_parser  # noqa

    top = create_parser()
    sp = _find_subparsers_action(top)
    if sp is None:
        raise RuntimeError("No subparsers found in create_parser().")

    commands = list(sp.choices.keys())  # preserve parser order

    # commands index
    idx = []
    idx.append("CLI reference")
    idx.append("=============")
    idx.append("")
    idx.append(".. toctree::")
    idx.append("   :maxdepth: 1")
    idx.append("")
    for c in commands:
        idx.append(f"   {c}")
    idx.append("")
    (out_dir / "index.rst").write_text("\n".join(idx), encoding="utf-8")

    for c in commands:
        cmd_parser = sp.choices[c]
        (out_dir / f"{c}.rst").write_text(render_command_rst(c, cmd_parser), encoding="utf-8")

    print(f"[OK] Generated {len(commands)} CLI pages in {out_dir}")


if __name__ == "__main__":
    main()
