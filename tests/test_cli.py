"""Tests for the command-line interface."""

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
