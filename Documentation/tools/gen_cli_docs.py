#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import argparse
import importlib.util
from pathlib import Path
from typing import Any, Iterable

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s or "")

def clean_help(s: str | None) -> str:
    if not s:
        return ""
    s = strip_ansi(s)

    # rimuovi marker tipo "-[required]" / "-[optional]" (case-insensitive)
    s = re.sub(r"^\s*-\s*\[(required|optional)\]\s*", "", s, flags=re.I)
    s = re.sub(r"\s*\[(required|optional)\]\s*", "", s, flags=re.I)

    # niente newline/bullets: tutto in una riga “plain”
    s = s.replace("\r", "\n")
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"^[\-\*\u2022]+\s*", "", s)  # - * • iniziali
    s = re.sub(r"\s+", " ", s).strip()
    return s

def cell(s: str) -> str:
    # cella “vuota” ma valida in list-table
    return s if s.strip() else r"\ "

def fmt_choices(ch: Any) -> str:
    if not ch:
        return ""
    try:
        return ", ".join(str(x) for x in list(ch))
    except TypeError:
        return str(ch)

def fmt_default(d: Any) -> str:
    if d is None or d is argparse.SUPPRESS:
        return ""
    return strip_ansi(str(d)).strip()

def _type_name(t: Any) -> str:
    if t is None:
        return ""
    if isinstance(t, type):
        return t.__name__
    return getattr(t, "__name__", str(t))

def fmt_type(action: argparse.Action) -> str:
    # bool flags
    if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        base = "bool"
    else:
        base = _type_name(getattr(action, "type", None))

        # inferenza semplice se non definito
        if not base and action.default not in (None, argparse.SUPPRESS):
            base = type(action.default).__name__

    # se nargs implica lista
    nargs = getattr(action, "nargs", None)
    if nargs in ("+", "*") or (isinstance(nargs, int) and nargs > 1):
        if base:
            return f"list[{base}]"
        return "list"
    return base

def is_required(action: argparse.Action) -> str:
    if action.option_strings:
        return "Yes" if getattr(action, "required", False) else "No"
    # positional
    nargs = getattr(action, "nargs", None)
    if nargs in ("?", "*"):
        return "No"
    return "Yes"

def fmt_option(action: argparse.Action) -> str:
    if action.option_strings:
        return ", ".join(f"``{o}``" for o in action.option_strings)
    return f"``{action.dest}``"

def get_actions(parser: argparse.ArgumentParser) -> list[argparse.Action]:
    out: list[argparse.Action] = []
    for a in parser._actions:
        # skip help
        if isinstance(a, argparse._HelpAction):
            continue
        out.append(a)
    return out

def positional_placeholders(actions: list[argparse.Action]) -> list[str]:
    pos = [a for a in actions if not a.option_strings and a.dest != "help"]
    ph: list[str] = []
    for a in pos:
        name = a.dest if a.dest else "arg"
        nargs = getattr(a, "nargs", None)
        if nargs == "?":
            ph.append(f"[<{name}>]")
        elif nargs == "*":
            ph.append(f"[<{name}> ...]")
        elif nargs == "+":
            ph.append(f"<{name}> ...")
        else:
            ph.append(f"<{name}>")
    return ph

def load_parser_module(parser_path: Path):
    os.environ["PYNTACLE_DOCS"] = "1"  # IMPORTANTISSIMO: niente colori ANSI

    spec = importlib.util.spec_from_file_location("pyntacle_parser", str(parser_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import parser module from {parser_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "create_parser"):
        raise RuntimeError("parser.py must expose create_parser()")
    return mod

def get_subparsers_action(p: argparse.ArgumentParser) -> argparse._SubParsersAction:
    for act in p._actions:
        if isinstance(act, argparse._SubParsersAction):
            return act
    raise RuntimeError("Top-level parser has no subparsers")

def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def rst_title(title: str, char: str = "=") -> str:
    return f"{title}\n{char*len(title)}\n"

def build_command_page(cmd: str, sp: argparse.ArgumentParser) -> str:
    desc = clean_help(getattr(sp, "description", "") or getattr(sp, "help", "") or "")
    actions = get_actions(sp)

    # synopsis “pulito”: niente ANSI, niente {a|b|c}
    ph = positional_placeholders(actions)
    syn = f"python3 main.py {cmd}"
    if ph:
        syn += " " + " ".join(ph)
    syn += " [OPTIONS]"

    # table rows: posizionali + opzionali, in ordine di definizione
    rows = []
    for a in actions:
        opt = fmt_option(a)
        req = is_required(a)
        typ = fmt_type(a)
        dft = fmt_default(getattr(a, "default", None))
        cho = fmt_choices(getattr(a, "choices", None))
        hlp = clean_help(getattr(a, "help", None))

        rows.append((opt, req, typ, dft, cho, hlp))

    # RST page
    out = []
    out.append(rst_title(cmd, "="))

    if desc:
        out.append(desc + "\n")

    out.append("Synopsis\n--------\n")
    out.append(".. code-block:: console\n\n")
    out.append(f"   {syn}\n\n")

    out.append("Options\n-------\n")
    out.append(".. list-table::\n")
    out.append("   :header-rows: 1\n")
    out.append("   :widths: 18 8 12 12 14 36\n\n")
    out.append("   * - Option\n")
    out.append("     - Required\n")
    out.append("     - Type\n")
    out.append("     - Default\n")
    out.append("     - Choices\n")
    out.append("     - Help\n")

    for (opt, req, typ, dft, cho, hlp) in rows:
        out.append(f"   * - {cell(opt)}\n")
        out.append(f"     - {cell(req)}\n")
        out.append(f"     - {cell(typ)}\n")
        out.append(f"     - {cell(strip_ansi(dft))}\n")
        out.append(f"     - {cell(strip_ansi(cho))}\n")
        out.append(f"     - {cell(strip_ansi(hlp))}\n")

    out.append("\n")
    return "".join(out)

def build_cli_index(commands: list[tuple[str, argparse.ArgumentParser]]) -> str:
    out = []
    out.append(rst_title("Command-line interface", "="))
    out.append(
        "Questa sezione documenta la CLI di Pyntacle (comandi e opzioni) "
        "come definita dal parser del progetto.\n\n"
    )

    # tabella “pulita” senza bullet list extra
    out.append("Commands\n--------\n")
    out.append(".. list-table::\n")
    out.append("   :header-rows: 1\n")
    out.append("   :widths: 20 80\n\n")
    out.append("   * - Command\n")
    out.append("     - Description\n")

    for cmd, sp in commands:
        desc = clean_help(getattr(sp, "description", "") or "")
        out.append(f"   * - :doc:`{cmd} <{cmd}/index>`\n")
        out.append(f"     - {cell(desc)}\n")

    out.append("\n")
    out.append(".. toctree::\n")
    out.append("   :maxdepth: 1\n")
    out.append("   :hidden:\n\n")
    for cmd, _ in commands:
        out.append(f"   {cmd}/index\n")
    out.append("\n")
    return "".join(out)

def build_home_dropdown(commands: list[tuple[str, argparse.ArgumentParser]]) -> str:
    # genera un include RST che crea: dropdown CLI + dropdown per ogni comando (ordine parser)
    out = []
    out.append("* .. raw:: html\n\n")
    out.append('     <details class="pyntacle-details">\n')
    out.append('     <summary><strong>Command-line interface</strong><span class="chev"></span></summary>\n')
    out.append('     <div class="pyntacle-details-body">\n\n')

    out.append("  :doc:`Open CLI overview <cli/index>`\n\n")

    for cmd, sp in commands:
        desc = clean_help(getattr(sp, "description", "") or "")
        out.append("  .. raw:: html\n\n")
        out.append('     <details class="pyntacle-details nested">\n')
        out.append(f'     <summary>{cmd}<span class="chev"></span></summary>\n')
        out.append('     <div class="pyntacle-details-body">\n\n')

        # contenuto RST dentro il <div>
        if desc:
            out.append(f"  {desc}\n\n")
        out.append(f"  :doc:`Open {cmd} <cli/{cmd}/index>`\n\n")

        out.append("  .. raw:: html\n\n")
        out.append("     </div>\n")
        out.append("     </details>\n\n")

    out.append("* .. raw:: html\n\n")
    out.append("     </div>\n")
    out.append("     </details>\n")
    out.append("\n")
    return "".join(out)

def main() -> int:
    docs_dir = Path(__file__).resolve().parents[1]          # .../Documentation
    repo_root = docs_dir.parent                             # .../pyntacle
    parser_path = repo_root / "pyntacle" / "parser.py"      # repo/pyntacle/parser.py
    source_dir = docs_dir / "source"
    cli_root = source_dir / "cli"

    mod = load_parser_module(parser_path)
    top = mod.create_parser()
    sub_action = get_subparsers_action(top)

    # ordine “come nel parser” (dict insertion order)
    commands: list[tuple[str, argparse.ArgumentParser]] = []
    for name, sp in sub_action.choices.items():
        commands.append((name, sp))

    # rigenera cartelle comando
    for cmd, sp in commands:
        cmd_dir = cli_root / cmd
        # pulizia della folder comando (solo se esiste)
        if cmd_dir.exists():
            for p in sorted(cmd_dir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    try:
                        p.rmdir()
                    except OSError:
                        pass
        cmd_dir.mkdir(parents=True, exist_ok=True)
        write_file(cmd_dir / "index.rst", build_command_page(cmd, sp))

    # rigenera cli/index.rst
    write_file(cli_root / "index.rst", build_cli_index(commands))

    # rigenera include per home page dropdown
    write_file(source_dir / "_parts" / "cli_dropdown.rst", build_home_dropdown(commands))

    print("[OK] CLI docs generated in Documentation/source/cli/")
    print("[OK] Home dropdown fragment: Documentation/source/_parts/cli_dropdown.rst")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
