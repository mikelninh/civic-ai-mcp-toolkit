"""
Error envelopes — the standardised shape every MCP tool returns instead of
raising. Lifted verbatim from the pattern that emerged across six MCPs.

The contract: an MCP tool must NEVER raise to the transport layer. A raise
crashes the request, may take down the server, and gives the LLM client an
unstructured error it cannot recover from. Instead, every error becomes a
structured dict the agent can read and act on.
"""

from __future__ import annotations

from typing import Any


def error_envelope(
    error: str,
    message: str = "",
    **extra: Any,
) -> dict[str, Any]:
    """
    Build a structured error response.

    Args:
      error:   short machine-readable error code ("not_found", "invalid_input",
               "internal_error", "rate_limited", "unauthorized", etc.).
      message: human-readable explanation, safe to surface to end users.
      **extra: any additional context fields that help the caller recover
               (e.g. `available=[...]` when the input was an unknown choice).

    Returns:
      {"error": <code>, "message": <text>, ...extra}

    Convention: `error` codes are snake_case strings. The set is open —
    domain-specific MCPs add their own (e.g. gitlaw-mcp uses
    "manifest_not_built", elterngeld-mcp uses "invalid_bezugs_art").
    """
    out: dict[str, Any] = {"error": error}
    if message:
        out["message"] = message
    out.update(extra)
    return out


# Common shorthand for the most frequent envelopes.


def not_found(resource: str, searched: Any) -> dict[str, Any]:
    return error_envelope("not_found", f"{resource} not found", searched=searched)


def invalid_input(field: str, reason: str, **extra: Any) -> dict[str, Any]:
    return error_envelope("invalid_input", f"{field}: {reason}", field=field, **extra)


def internal_error(exception: BaseException) -> dict[str, Any]:
    """Surface an internal exception as a clean envelope. Used by @traced."""
    return error_envelope(
        "internal_error",
        f"{type(exception).__name__}: {exception}",
    )
