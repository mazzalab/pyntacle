"""The option table of every command page matches the parser.

The pages are written by hand around their option table, so nothing keeps
them in step with ``pyntacle/parser.py`` but this test: every option the
parser accepts has a row, no row names an option the parser lacks, and the
default and choices agree. Help texts may be reworded in the docs.
"""
import argparse
import os
import re

import pytest

from pyntacle.parser import create_parser

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Documentation", "source", "cli")


def subcommands():
    action = next(a for a in create_parser()._actions if isinstance(a, argparse._SubParsersAction))
    return action.choices


def doc_rows(command):
    """{option strings: {column header: cell}} from the page's Options list-table."""
    text = open(os.path.join(DOCS, command, "index.rst"), encoding="utf-8").read()
    table = text[text.index("Options\n-------\n"):]
    next_section = re.search(r"\n[^\n]+\n-{3,}\n", table[20:])
    if next_section:
        table = table[:next_section.start() + 20]
    rows = re.findall(r"   \* - (.*?)(?=\n   \* - |\Z)", table, flags=re.S)
    cells = [[c.strip() for c in re.split(r"\n     - ", r)] for r in rows]
    header, body = cells[0], cells[1:]
    return {tuple(re.findall(r"``([^`]+)``", r[0])) or (r[0],): dict(zip(header, r)) for r in body}


def text(value):
    value = value.replace("``", "").strip()
    return "" if value in ("\\", "\\ ", "False") else value


def same_default(doc, default):
    """A default of None is resolved at run time, so the page may describe it in words."""
    if default is None:
        return True
    if default is False:
        return doc == ""
    try:
        return float(doc) == float(default)
    except (TypeError, ValueError):
        return doc == str(default)


# the omics page documents its two pipelines in prose, not as a table row
UNTABLED = {("omics", "subcommand")}


@pytest.mark.parametrize("command", sorted(subcommands()))
def test_every_option_has_a_matching_row(command):
    parser = subcommands()[command]
    rows = doc_rows(command)
    documented = {s for key in rows for s in key}
    problems = []
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue
        names = tuple(action.option_strings) or ("subcommand",)
        row = next((rows[k] for k in rows if set(names) & set(k)), None)
        if row is None:
            if (command, names[0]) not in UNTABLED:
                problems.append(f"{'/'.join(names)}: no row")
            continue
        documented -= set(names)
        if action.choices and "Choices" in row:
            if [c.strip() for c in text(row["Choices"]).split(",")] != [str(c) for c in action.choices]:
                problems.append(f"{'/'.join(names)}: choices {row['Choices']!r} != {list(action.choices)}")
        if "Default" in row and action.option_strings and not isinstance(action, argparse._StoreTrueAction):
            if not same_default(text(row["Default"]), action.default):
                problems.append(f"{'/'.join(names)}: default {row['Default']!r} != {action.default!r}")
    problems += [f"{name}: row for an option the parser lacks" for name in sorted(documented)
                 if name.startswith("-")]
    assert not problems, f"{command}: " + "; ".join(problems)
