"""Tests for the command-line interface."""

from pathlib import Path

from statute_watch.cli import main


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
