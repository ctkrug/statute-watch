"""Command-line entrypoint for Statute Watch.

Subcommands:
    validate   Load and validate the dataset + provenance (exit 1 on error).
    build      Render the static site into an output directory.
    list       Print tracked statutes to the terminal, optionally filtered.
    sources    List the registered legislative sources.
    fetch      Stage candidate bills from a source feed (never touches curated data).
    diff       Report how a staging file differs from the current dataset.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .build import DEFAULT_OUTPUT_DIR, build_site
from .catalog import load_catalog
from .models import ValidationError
from .pipeline import (
    PipelineError,
    apply_merge,
    diff,
    fetch,
    load_staging,
    staging_path,
)
from .sources import check_provenance, load_sources
from .summarize import stage_label, status_line


def _cmd_validate(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.data)
    registry = load_sources(args.sources)
    check_provenance(catalog, registry)
    counts = catalog.category_counts()
    print(f"OK — {len(catalog)} statutes across {len(catalog.states())} states.")
    for category, count in counts.items():
        if count:
            print(f"  {category:<14} {count}")
    print(f"  provenance     {len(registry.official())} official sources")
    return 0


def _cmd_sources(args: argparse.Namespace) -> int:
    registry = load_sources(args.sources)
    for source in registry:
        tag = source.state or source.jurisdiction
        print(f"{source.kind:<9} {tag:<16} {source.name}")
        print(f"          {source.url}")
    return 0


def _cmd_fetch(args: argparse.Namespace) -> int:
    registry = load_sources(args.sources)
    out = fetch(
        args.source,
        registry=registry,
        feed=args.feed,
        staging_dir=args.staging_dir,
        allow_network=args.network,
    )
    staged = load_staging(out)
    print(f"Staged {len(staged)} candidate(s) from {args.source} -> {out}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    catalog = load_catalog(args.data)
    if not args.staging and not args.source:
        raise PipelineError("diff needs a source id or an explicit --staging path")
    path = args.staging or staging_path(args.source, args.staging_dir)
    report = diff(catalog, load_staging(path))
    if not report.entries:
        print("No staged candidates to compare.")
        return 0
    for entry in report.new:
        print(f"NEW      {entry.id}  ({entry.detail})")
    for entry in report.advanced:
        print(f"ADVANCED {entry.id}  ({entry.detail})")
    for entry in report.unchanged:
        print(f"same     {entry.id}")
    print(
        f"\n{len(report.new)} new, {len(report.advanced)} advanced, "
        f"{len(report.unchanged)} unchanged."
    )
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    import yaml

    catalog = load_catalog(args.data)
    if not args.staging and not args.source:
        raise PipelineError("merge needs a source id or an explicit --staging path")
    path = args.staging or staging_path(args.source, args.staging_dir)
    staged = load_staging(path)
    report = diff(catalog, staged)

    if not report.has_changes():
        print("Nothing to merge — no new or advanced records.")
        return 0

    print(f"Would apply {len(report.new)} new and {len(report.advanced)} advanced record(s):")
    for entry in report.new + report.advanced:
        print(f"  {entry.kind:<13} {entry.id}  ({entry.detail})")

    if not args.write:
        print("\nPreview only. Re-run with --write to update the dataset.")
        return 0

    merged = apply_merge(catalog, staged)
    target = args.out or args.data or _default_data_path()
    target.write_text(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True), encoding="utf-8")
    # Re-validate the written dataset so a merge can never ship a broken file.
    reloaded = load_catalog(target)
    print(f"\nWrote {len(reloaded)} statutes -> {target} (revalidated OK).")
    return 0


def _default_data_path() -> Path:
    from .catalog import DEFAULT_DATA_PATH

    return DEFAULT_DATA_PATH


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
    parser.add_argument(
        "--sources",
        type=Path,
        default=None,
        help="path to a sources YAML registry (defaults to the bundled registry)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate the dataset and its provenance")
    p_validate.set_defaults(func=_cmd_validate)

    p_sources = sub.add_parser("sources", help="list the registered legislative sources")
    p_sources.set_defaults(func=_cmd_sources)

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

    p_fetch = sub.add_parser("fetch", help="stage candidate bills from a source feed")
    p_fetch.add_argument("source", help="a registered source id (see `sources`)")
    p_fetch.add_argument("--feed", type=Path, help="local feed file to read (the offline path)")
    p_fetch.add_argument(
        "--network", action="store_true", help="opt in to live fetching (off by default)"
    )
    p_fetch.add_argument("--staging-dir", type=Path, help="staging directory override")
    p_fetch.set_defaults(func=_cmd_fetch)

    p_diff = sub.add_parser("diff", help="diff a staging file against the dataset")
    p_diff.add_argument("source", nargs="?", help="source id whose staged file to diff")
    p_diff.add_argument("--staging", type=Path, help="explicit staging file path")
    p_diff.add_argument("--staging-dir", type=Path, help="staging directory override")
    p_diff.set_defaults(func=_cmd_diff)

    p_merge = sub.add_parser(
        "merge", help="fold staged new/advanced records into the dataset (preview by default)"
    )
    p_merge.add_argument("source", nargs="?", help="source id whose staged file to merge")
    p_merge.add_argument("--staging", type=Path, help="explicit staging file path")
    p_merge.add_argument("--staging-dir", type=Path, help="staging directory override")
    p_merge.add_argument("--write", action="store_true", help="apply the merge (default: preview)")
    p_merge.add_argument("--out", type=Path, help="write merged dataset here instead of in place")
    p_merge.set_defaults(func=_cmd_merge)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, FileNotFoundError, PipelineError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
