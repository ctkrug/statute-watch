"""Shared pytest fixtures and path setup for the Statute Watch suite."""

import sys
from pathlib import Path

import pytest

# Make the src/ layout importable without an editable install (keeps CI + local
# runs identical and dependency-free beyond the declared deps).
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from statute_watch.catalog import load_catalog  # noqa: E402


@pytest.fixture
def catalog():
    """The bundled dataset, loaded and validated."""
    return load_catalog()
