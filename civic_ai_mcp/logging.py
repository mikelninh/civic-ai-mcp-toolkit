"""
Structured JSON logging — one line per tool call, parseable by anything.

Format mirrors what gitlaw-mcp, safevoice-mcp, pmm-mcp etc. all log:

    {"ts":"2026-05-29T12:34:56","level":"INFO","logger":"...","msg":"tool.X",
     "request_id":"abc12345","tool":"X","latency_ms":12.3,"status":"ok"}

This shape is what the `traced` decorator emits via `log_json`. Stays on
stderr so stdio MCP transport (which uses stdout for JSON-RPC) isn't
disturbed.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any


def configure_logging(
    *,
    level: str | None = None,
    logger_name: str = "civic_ai_mcp",
) -> logging.Logger:
    """
    Set up the project-wide logger with stderr handler and ISO timestamps.

    Args:
      level: log level string. Defaults to env LOG_LEVEL, then "INFO".
      logger_name: namespace prefix; per-server loggers like "judge_mcp",
                   "gitlaw_mcp" inherit through dot-notation.

    Returns the logger so callers can attach extra handlers if needed.
    """
    effective = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=effective,
        format="%(message)s",
        stream=sys.stderr,
    )
    return logging.getLogger(logger_name)


def log_json(logger: logging.Logger, level: int, **fields: Any) -> None:
    """
    Emit a single structured-JSON log line. Always includes `ts`. Other
    fields passed as kwargs.
    """
    fields.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    logger.log(level, json.dumps(fields, ensure_ascii=False))
