"""
@traced decorator — request-id + latency + structured-log envelope around
every MCP tool. Distilled from the variant that appears (slightly different
each time) in gitlaw-mcp, safevoice-mcp, pmm-mcp, judge-mcp, elterngeld-mcp.

The pattern:
  - Generate a 12-char request_id per call (collision-safe enough for logs)
  - Time the call
  - On success: log status="ok" with latency
  - On exception: log status="error", return a clean error envelope (the
    tool NEVER raises to the MCP transport)

Usage:

    from civic_ai_mcp import traced

    @mcp.tool()
    @traced("my_tool")
    def my_tool(query: str) -> dict:
        ...

The `@mcp.tool()` MUST be on top (outer) so the MCP framework registers
the wrapped function. `@traced(...)` is the inner decorator.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable

from civic_ai_mcp.envelope import internal_error
from civic_ai_mcp.logging import log_json

_DEFAULT_LOGGER_NAME = "civic_ai_mcp"


def traced(
    tool_name: str,
    *,
    logger_name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Wrap a tool function with the canonical request-id + latency + clean-error
    envelope pattern.

    Args:
      tool_name:   short identifier that appears in logs as `tool.<name>`.
      logger_name: which logger to write to (default "civic_ai_mcp"). Set per
                   server to keep logs separable when multiple MCPs run in
                   the same process.
    """
    logger = logging.getLogger(logger_name or _DEFAULT_LOGGER_NAME)

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_id = uuid.uuid4().hex[:12]
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                log_json(
                    logger,
                    logging.INFO,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="ok",
                )
                return result
            except Exception as e:  # pragma: no cover — defensive contract
                log_json(
                    logger,
                    logging.ERROR,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="error",
                    error=f"{type(e).__name__}: {e}",
                )
                return internal_error(e)

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        return wrapper

    return decorator
