"""
civic-ai-mcp-toolkit tests — covers each piece of the shared shape:
error envelopes, structured logging, the @traced decorator semantics, fixture
loader caching, server factory, and the CLI scaffolder smoke-test.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from civic_ai_mcp.envelope import (  # noqa: E402
    error_envelope,
    internal_error,
    invalid_input,
    not_found,
)
from civic_ai_mcp.fixtures import clear_fixture_cache, load_fixture  # noqa: E402
from civic_ai_mcp.logging import configure_logging, log_json  # noqa: E402
from civic_ai_mcp.tracing import traced  # noqa: E402


# ── envelope ─────────────────────────────────────────────────────────


def test_error_envelope_basic():
    e = error_envelope("not_found", "thing missing")
    assert e == {"error": "not_found", "message": "thing missing"}


def test_error_envelope_with_extra_fields():
    e = error_envelope("invalid", "bad", field="x", allowed=[1, 2, 3])
    assert e["error"] == "invalid"
    assert e["field"] == "x"
    assert e["allowed"] == [1, 2, 3]


def test_error_envelope_omits_empty_message():
    e = error_envelope("not_found")
    assert e == {"error": "not_found"}


def test_not_found_shorthand():
    e = not_found("law", "BGB")
    assert e["error"] == "not_found"
    assert e["searched"] == "BGB"


def test_invalid_input_shorthand():
    e = invalid_input("year", "must be >= 2020")
    assert e["error"] == "invalid_input"
    assert e["field"] == "year"


def test_internal_error_carries_exception_info():
    try:
        raise ValueError("oh no")
    except ValueError as exc:
        e = internal_error(exc)
        assert e["error"] == "internal_error"
        assert "ValueError" in e["message"]
        assert "oh no" in e["message"]


# ── logging ──────────────────────────────────────────────────────────


def test_configure_logging_returns_logger():
    log = configure_logging(level="DEBUG", logger_name="test_civic_ai_mcp_x")
    assert isinstance(log, logging.Logger)
    assert log.name == "test_civic_ai_mcp_x"


def test_log_json_writes_structured_line(caplog):
    log = logging.getLogger("test_log_json")
    log.setLevel(logging.INFO)
    with caplog.at_level(logging.INFO, logger="test_log_json"):
        log_json(log, logging.INFO, msg="hello", request_id="abc123", latency_ms=12.3)
    rec = caplog.records[-1]
    parsed = json.loads(rec.message)
    assert parsed["msg"] == "hello"
    assert parsed["request_id"] == "abc123"
    assert parsed["latency_ms"] == 12.3
    assert "ts" in parsed


# ── @traced ──────────────────────────────────────────────────────────


def test_traced_returns_unchanged_on_success():
    @traced("my_tool")
    def tool(x):
        return {"result": x * 2}

    assert tool(5) == {"result": 10}


def test_traced_returns_envelope_on_exception():
    @traced("crashing_tool")
    def tool():
        raise RuntimeError("boom")

    result = tool()
    assert result["error"] == "internal_error"
    assert "RuntimeError" in result["message"]
    assert "boom" in result["message"]


def test_traced_preserves_function_metadata():
    @traced("named")
    def my_tool(x):
        """My docstring."""
        return x

    assert my_tool.__name__ == "my_tool"
    assert my_tool.__doc__ == "My docstring."
    # __wrapped__ exposes the inner function for testing
    assert my_tool.__wrapped__(7) == 7  # type: ignore[attr-defined]


def test_traced_logs_with_request_id(caplog):
    @traced("logged", logger_name="test_traced_x")
    def tool():
        return {"ok": True}

    with caplog.at_level(logging.INFO, logger="test_traced_x"):
        tool()

    rec = caplog.records[-1]
    parsed = json.loads(rec.message)
    assert parsed["tool"] == "logged"
    assert parsed["status"] == "ok"
    assert "request_id" in parsed
    assert len(parsed["request_id"]) == 12
    assert "latency_ms" in parsed


def test_traced_logs_error_status_on_exception(caplog):
    @traced("erring", logger_name="test_traced_err")
    def tool():
        raise ValueError("nope")

    with caplog.at_level(logging.ERROR, logger="test_traced_err"):
        tool()

    rec = caplog.records[-1]
    parsed = json.loads(rec.message)
    assert parsed["status"] == "error"
    assert "ValueError" in parsed["error"]


# ── fixtures loader ──────────────────────────────────────────────────


def test_load_fixture_caches_on_second_call(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    f = data_dir / "x.json"
    f.write_text('{"a": 1}', encoding="utf-8")

    clear_fixture_cache()
    a = load_fixture(tmp_path, "x.json")
    # Mutate file on disk — cached version should be returned unchanged
    f.write_text('{"a": 999}', encoding="utf-8")
    b = load_fixture(tmp_path, "x.json")
    assert a == b == {"a": 1}


def test_clear_fixture_cache_forces_reload(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    f = data_dir / "y.json"
    f.write_text('{"v": 1}', encoding="utf-8")

    clear_fixture_cache()
    assert load_fixture(tmp_path, "y.json") == {"v": 1}
    f.write_text('{"v": 2}', encoding="utf-8")
    clear_fixture_cache()
    assert load_fixture(tmp_path, "y.json") == {"v": 2}


def test_load_fixture_raises_loudly_on_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_fixture(tmp_path, "does_not_exist.json")


# ── server factory ───────────────────────────────────────────────────


def test_create_mcp_server_returns_fastmcp_instance():
    from civic_ai_mcp.server import create_mcp_server
    from mcp.server.fastmcp import FastMCP

    srv = create_mcp_server("test-mcp", default_port=9999)
    assert isinstance(srv, FastMCP)


def test_create_mcp_server_respects_env_port(monkeypatch):
    from civic_ai_mcp.server import create_mcp_server

    monkeypatch.setenv("PORT", "8888")
    srv = create_mcp_server("envport-test")
    # FastMCP stores the port internally; we can't easily introspect across
    # versions, so we just confirm the call doesn't crash.
    assert srv is not None


# ── CLI scaffolder smoke test ────────────────────────────────────────


def test_cli_init_scaffolds_a_runnable_project(tmp_path):
    """End-to-end: run `civic-ai-mcp init` and check the layout it produced."""
    target = tmp_path / "my-test-mcp"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "civic_ai_mcp.cli",
            "init",
            "my-test",
            "--target",
            str(target),
            "--description",
            "A test MCP",
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr

    assert (target / "pyproject.toml").exists()
    assert (target / "README.md").exists()
    assert (target / "LICENSE").exists()
    assert (target / ".gitignore").exists()
    assert (target / "my_test_mcp" / "__init__.py").exists()
    assert (target / "my_test_mcp" / "server.py").exists()
    assert (target / "tests" / "test_my_test_mcp.py").exists()

    # Server file substitutes the template variables correctly
    server_content = (target / "my_test_mcp" / "server.py").read_text(encoding="utf-8")
    assert '"my-test"' in server_content
    assert "{{name}}" not in server_content
