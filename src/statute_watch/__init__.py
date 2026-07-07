"""Statute Watch — tracker of US state privacy-law changes.

The package is a small, dependency-light pipeline: it loads a curated dataset of
state privacy statutes (:mod:`statute_watch.catalog`), models them
(:mod:`statute_watch.models`), derives plain-English summaries
(:mod:`statute_watch.summarize`), and renders a static, self-contained site
(:mod:`statute_watch.build`).
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
