"""Tests for the command-line interface."""

from pathlib import Path

from statute_watch.catalog import DEFAULT_DATA_PATH
from statute_watch.cli import _default_data_path, main


def test_default_data_path_points_at_bundled_dataset():
    assert _default_data_path() == DEFAULT_DATA_PATH


def test_validate_ok(capsys):
    assert main(["validate"]) == 0
    out = capsys.readouterr().out
    assert "statutes across" in out


def test_build_writes_site(tmp_path, capsys):
    assert main(["build", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "index.html").exists()
    assert "Built" in capsys.readouterr().out


def test_list_filtered_by_state(capsys):
    assert main(["list", "--state", "il"]) == 0
    out = capsys.readouterr().out
    assert "IL" in out
    assert "Biometric Information Privacy Act" in out


def test_validate_bad_dataset_exits_nonzero(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- id: x\n  state: ZZ\n  categories: [biometric]\n", encoding="utf-8")
    assert main(["--data", str(bad), "validate"]) == 1
    assert "error:" in capsys.readouterr().err


def test_validate_reports_provenance(capsys):
    assert main(["validate"]) == 0
    assert "official sources" in capsys.readouterr().out


def test_validate_fails_without_official_source(tmp_path, capsys):
    # A state absent from the source registry must fail the provenance gate.
    data = tmp_path / "d.yaml"
    data.write_text(
        "- id: ak-1\n  state: AK\n  title: T\n  bill_number: HB 1\n"
        "  categories: [comprehensive]\n  stage: introduced\n  summary: S.\n"
        "  source_url: https://akleg.gov/hb1\n",
        encoding="utf-8",
    )
    assert main(["--data", str(data), "validate"]) == 1
    assert "AK" in capsys.readouterr().err


def test_sources_lists_registry(capsys):
    assert main(["sources"]) == 0
    out = capsys.readouterr().out
    assert "official" in out
    assert "California Legislative Information" in out


FEED = str(Path(__file__).resolve().parent / "fixtures" / "feed_ncsl_sample.yaml")


def test_fetch_then_diff_roundtrip(tmp_path, capsys):
    assert main(
        ["fetch", "congress-ncsl", "--feed", FEED, "--staging-dir", str(tmp_path)]
    ) == 0
    assert "Staged 3 candidate" in capsys.readouterr().out

    assert main(["diff", "congress-ncsl", "--staging-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NEW      ny-s-365-2025" in out
    assert "ADVANCED ny-s-1042-2025" in out
    assert "1 new, 1 advanced, 1 unchanged." in out


def test_fetch_network_guard_exits_nonzero(tmp_path, capsys):
    assert main(["fetch", "congress-ncsl", "--staging-dir", str(tmp_path)]) == 1
    assert "network is disabled" in capsys.readouterr().err


def test_diff_without_target_exits_nonzero(capsys):
    assert main(["diff"]) == 1
    assert "source id or an explicit --staging" in capsys.readouterr().err


def test_merge_preview_does_not_write(tmp_path, capsys):
    main(["fetch", "congress-ncsl", "--feed", FEED, "--staging-dir", str(tmp_path)])
    capsys.readouterr()
    out_data = tmp_path / "merged.yaml"
    assert main(["merge", "congress-ncsl", "--staging-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Preview only" in out
    assert not out_data.exists()


def test_list_filtered_by_category(capsys):
    assert main(["list", "--category", "biometric"]) == 0
    out = capsys.readouterr().out
    assert "Biometric Information Privacy Act" in out


def test_list_no_matches_reports_cleanly(capsys):
    # A filter that matches nothing prints a message and still exits 0.
    assert main(["list", "--state", "AK"]) == 0
    assert "No statutes match." in capsys.readouterr().out


def test_diff_empty_staging_reports_nothing(tmp_path, capsys):
    staging = tmp_path / "congress-ncsl.yaml"
    staging.write_text("[]\n", encoding="utf-8")
    assert main(["diff", "congress-ncsl", "--staging-dir", str(tmp_path)]) == 0
    assert "No staged candidates to compare." in capsys.readouterr().out


def test_merge_without_target_exits_nonzero(capsys):
    assert main(["merge"]) == 1
    assert "source id or an explicit --staging" in capsys.readouterr().err


def test_merge_nothing_to_merge(tmp_path, capsys):
    staging = tmp_path / "congress-ncsl.yaml"
    staging.write_text("[]\n", encoding="utf-8")
    assert main(["merge", "congress-ncsl", "--staging-dir", str(tmp_path)]) == 0
    assert "Nothing to merge" in capsys.readouterr().out


def test_merge_write_refuses_to_break_provenance(tmp_path, capsys):
    # A staged bill for a state with no official source must not be merged in:
    # the written dataset would fail the validate gate, so merge must refuse and
    # not write the file (a merge can never ship a broken dataset).
    staging = tmp_path / "src.yaml"
    staging.write_text(
        "- id: ak-new-1\n  state: AK\n  title: Alaska Biometric Privacy Act\n"
        "  bill_number: HB 99\n  categories: [biometric]\n  stage: introduced\n"
        "  summary: A new Alaska bill with no registered source.\n"
        "  source_url: https://akleg.gov/hb99\n  fetched_from: congress-ncsl\n",
        encoding="utf-8",
    )
    out_data = tmp_path / "merged.yaml"
    argv = ["merge", "--staging", str(staging), "--write", "--out", str(out_data)]
    assert main(argv) == 1
    assert "AK" in capsys.readouterr().err
    assert not out_data.exists()


def test_merge_write_applies_and_revalidates(tmp_path, capsys):
    main(["fetch", "congress-ncsl", "--feed", FEED, "--staging-dir", str(tmp_path)])
    capsys.readouterr()
    out_data = tmp_path / "merged.yaml"
    argv = ["merge", "congress-ncsl", "--staging-dir", str(tmp_path)]
    argv += ["--write", "--out", str(out_data)]
    assert main(argv) == 0
    assert "revalidated OK" in capsys.readouterr().out
    assert out_data.exists()
    # The written dataset validates on its own.
    assert main(["--data", str(out_data), "validate"]) == 0
