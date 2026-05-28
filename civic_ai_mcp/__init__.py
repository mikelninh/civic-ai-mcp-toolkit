"""
civic-ai-mcp-toolkit — the shared shape behind every MCP in the portfolio.

Built by extracting the recurring pattern from six production MCPs
(gitlaw-mcp, safevoice-mcp, grailsense, judge-mcp, pmm-mcp, elterngeld-mcp).
The first machine that builds machines — M1 from the Digital Democracy
Studio thesis.

Public surface:

    from civic_ai_mcp import (
        create_mcp_server,
        traced,
        load_fixture,
        error_envelope,
        configure_logging,
    )

    mcp = create_mcp_server("my-new-mcp", default_port=8010)
    configure_logging()

    @mcp.tool()
    @traced("my_tool")
    def my_tool(query: str) -> dict:
        ...

That's it. Health endpoint, structured JSON logging, error envelopes,
host/port from env vars, and stdio/SSE transport selection are all set up
for you. A new MCP server is now a one-day build instead of a one-weekend
build.
"""

from civic_ai_mcp.envelope import error_envelope
from civic_ai_mcp.fixtures import load_fixture
from civic_ai_mcp.logging import configure_logging, log_json
from civic_ai_mcp.server import create_mcp_server, run_main
from civic_ai_mcp.tracing import traced

__all__ = [
    "create_mcp_server",
    "run_main",
    "traced",
    "load_fixture",
    "error_envelope",
    "configure_logging",
    "log_json",
]

__version__ = "0.1.0"
