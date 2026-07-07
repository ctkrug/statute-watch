"""Command-line entrypoint for Statute Watch.

Subcommands:
    validate   Load and validate the dataset; report counts (exit 1 on error).
    build      Render the static site into an output directory.
    list       Print tracked statutes to the terminal, optionally filtered.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .build import DEFAULT_OUTPUT_DIR, build_site
from .catalog import load_catalog
from .models import ValidationError
from .summarize import stage_label, status_line


def _cmd_validate(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.data)
    counts = catalog.category_counts()
    print(f"OK — {len(catalog)} statutes across {len(catalog.states())} states.")
    for category, count in counts.items():
        if count:
            print(f"  {category:<14} {count}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.data)
    out = build_site(args.output, catalog=catalog)
    print(f"Built {len(catalog)} statutes -> {out}/index.html")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.data)
    rows = list(catalog)
    if args.state:
        rows = [s for s in rows if s.state == args.state.upper()]
    if args.category:
        rows = [s for s in rows if args.category in s.categories]
    if not rows:
        print("No statutes match.")
        return 0
    for s in rows:
        print(f"{s.state}  {s.bill_number:<12}  {stage_label(s):<11}  {s.title}")
        print(f"      {status_line(s)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="statute-watch",
        description="Tracker of US state privacy-law changes.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="path to a statutes YAML dataset (defaults to the bundled dataset)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate the dataset")
    p_validate.set_defaults(func=_cmd_validate)

    p_build = sub.add_parser("build", help="render the static site")
    p_build.add_argument(
        "output",
        nargs="?",
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help=f"output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    p_build.set_defaults(func=_cmd_build)

    p_list = sub.add_parser("list", help="list tracked statutes")
    p_list.add_argument("--state", help="filter by two-letter state code")
    p_list.add_argument("--category", help="filter by data-type category")
    p_list.set_defaults(func=_cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
