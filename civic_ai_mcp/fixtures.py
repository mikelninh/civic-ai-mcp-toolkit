"""
Fixture loader — the JSON-bundled-data pattern that ships with most MCPs.

gitlaw-mcp ships rubrics + manifest, pmm-mcp ships budget + BRH findings,
elterngeld-mcp ships bundeslaender, judge-mcp ships rubrics. They all do
exactly the same thing: load a versioned JSON file from a `data/` directory
next to the server module, cache it on first read.

This utility extracts that pattern so each new MCP doesn't reinvent it.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_cache: dict[str, Any] = {}
_lock = threading.Lock()


def load_fixture(
    package_root: Path,
    filename: str,
    *,
    subdir: str = "data",
) -> Any:
    """
    Load a JSON fixture from <package_root>/<subdir>/<filename>. Cached.

    Args:
      package_root: pass `Path(__file__).resolve().parent` from the calling
                    server module.
      filename:     e.g. "budget.json", "rubrics.json".
      subdir:       defaults to "data" — the convention across the portfolio.

    Returns:
      Parsed JSON. Cached on first successful load — subsequent calls are
      free. Cache key includes the full path so multiple MCPs in the same
      process don't collide.

    Raises:
      FileNotFoundError if the file is missing. We don't wrap this — fixture
      absence is a deployment bug, not a runtime envelope. Surface it loudly.
    """
    path = package_root / subdir / filename
    key = str(path)

    with _lock:
        if key in _cache:
            return _cache[key]
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        _cache[key] = data
        return data


def clear_fixture_cache() -> None:
    """Reset the cache — primarily useful in tests that mutate fixture files."""
    with _lock:
        _cache.clear()
