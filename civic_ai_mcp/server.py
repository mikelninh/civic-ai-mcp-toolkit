"""
FastMCP server factory + /health endpoint + main() entry point.

Distills the construction pattern that every MCP in the portfolio repeats:
  mcp = FastMCP(name, host=..., port=...)
  try: register /health route
  def main(): pick stdio vs sse via MCP_TRANSPORT env var
"""

from __future__ import annotations

import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP


def create_mcp_server(
    name: str,
    *,
    default_port: int = 8000,
    health_service_label: str | None = None,
) -> FastMCP:
    """
    Build a FastMCP server with the shared portfolio conventions wired in:
      - host/port bound from env (FASTMCP_HOST / FASTMCP_PORT / PORT) with
        sensible defaults — 0.0.0.0 so SSE health checks reach in from
        outside the container
      - a /health route returning {"status": "ok", "service": <name>} for
        Fly.io / Railway / Cloud Run health-probe compatibility

    Args:
      name:                 short service name (e.g. "gitlaw", "judge").
                            Shows up in health response and MCP handshake.
      default_port:         what to bind when no PORT env var is set.
      health_service_label: optional override of the `service` field in
                            health JSON. Defaults to `name`.
    """
    mcp = FastMCP(
        name,
        host=os.getenv("FASTMCP_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTMCP_PORT", os.getenv("PORT", str(default_port)))),
    )

    # Health endpoint — only register if Starlette+custom_route are available.
    try:
        from starlette.responses import JSONResponse  # type: ignore

        label = health_service_label or f"{name}-mcp"

        @mcp.custom_route("/health", methods=["GET"])
        async def _health(_request: Any) -> JSONResponse:
            return JSONResponse({"status": "ok", "service": label})
    except Exception:  # pragma: no cover — older FastMCP without custom_route
        pass

    return mcp


def run_main(mcp: FastMCP) -> None:
    """
    Standard entry point. Picks transport from MCP_TRANSPORT env var:
      stdio (default)   — Claude Desktop, Cursor, local clients
      sse / streamable-http — hosted clients via HTTP+SSE

    Logging is set up by the caller (or via civic_ai_mcp.configure_logging()).
    We don't double-configure here so the caller stays in control of format
    and verbosity.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport)
    else:
        mcp.run()


def cli_main_template(mcp: FastMCP) -> int:
    """
    Optional convenience: pre-configures stderr-based JSON logging and runs.
    Equivalent to the `def main()` pattern in every MCP server.py.

    Returns 0 on clean exit; non-zero only on hard failure.
    """
    from civic_ai_mcp.logging import configure_logging

    configure_logging()
    try:
        run_main(mcp)
        return 0
    except KeyboardInterrupt:  # pragma: no cover
        print("interrupted", file=sys.stderr)
        return 130
