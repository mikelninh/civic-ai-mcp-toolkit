# civic-ai-mcp-toolkit

**The shared shape behind every MCP server in the civic-AI portfolio.** Server factory, `@traced` decorator, structured logging, error envelopes, fixture loader, and a `civic-ai-mcp init` CLI scaffolder — all distilled from six production MCPs.

[![Tests](https://img.shields.io/badge/tests-19%2F19-brightgreen?logo=pytest)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-toolkit-blue)](https://modelcontextprotocol.io)

---

## Why it exists

After building six MCP servers ([gitlaw](https://github.com/mikelninh/gitlaw), [safevoice](https://github.com/mikelninh/safevoice), [grailsense](https://github.com/mikelninh/grailsense), [judge-mcp](https://github.com/mikelninh/judge-mcp), [pmm-mcp](https://github.com/mikelninh/pmm-mcp), [elterngeld-mcp](https://github.com/mikelninh/elterngeld-mcp)) in one weekend, the same ~50 lines kept repeating in every `server.py`:

- FastMCP construction with env-based host/port
- A `@traced` decorator that wraps every tool with request-id + latency + structured-JSON logging
- A `/health` endpoint for hosted-deploy probes
- Clean error envelopes that never raise to the MCP transport
- A `main()` that picks stdio vs SSE from `MCP_TRANSPORT`
- A fixture-loader that caches JSON files from `data/`

This package extracts that shape **once** so future MCPs are a one-day build, not a one-weekend build.

It's the first "machine that builds machines" from the [Digital Democracy Studio](https://github.com/mikelninh/wiki) thesis — M1 in the studio's missing-machines list.

---

## Minimum example

```python
from civic_ai_mcp import configure_logging, create_mcp_server, run_main, traced

mcp = create_mcp_server("my-cool-mcp", default_port=8010)


@mcp.tool()
@traced("hello")
def hello(name: str = "world") -> dict:
    """Greet someone."""
    return {"greeting": f"Hello, {name}!"}


def main() -> None:
    configure_logging(logger_name="my_cool_mcp")
    run_main(mcp)


if __name__ == "__main__":
    main()
```

That's the full server. You get for free:
- `/health` returning `{"status": "ok", "service": "my-cool-mcp"}`
- Per-tool JSON log lines: `{"ts": "...", "tool": "hello", "request_id": "abc12345", "latency_ms": 1.2, "status": "ok"}`
- `hello` returning a structured error envelope instead of raising if anything goes wrong inside
- stdio mode for Claude Desktop (default) + SSE mode if `MCP_TRANSPORT=sse`
- Host bound to `0.0.0.0` so hosted health probes can reach it

---

## CLI: scaffold a new MCP project

```bash
pip install civic-ai-mcp-toolkit
civic-ai-mcp init flight-rights --description "EU261 flight compensation calculator" --port 8011
cd flight-rights-mcp
pip install -e .
pytest
```

You get a complete project layout:

```
flight-rights-mcp/
├── flight_rights_mcp/
│   ├── __init__.py
│   ├── data/
│   └── server.py          # sample tool, uses civic_ai_mcp helpers
├── tests/
│   └── test_flight_rights_mcp.py
├── pyproject.toml         # standard portfolio shape
├── README.md              # stub with install instructions
├── LICENSE                # MIT
└── .gitignore
```

Replace the sample tool, add data fixtures to `data/`, ship.

---

## Public surface

```python
from civic_ai_mcp import (
    create_mcp_server,    # build a FastMCP with portfolio defaults
    run_main,             # standard entry-point (stdio | SSE from env)
    traced,               # @traced("tool_name") decorator
    configure_logging,    # stderr JSON logging setup
    log_json,             # emit one structured log line
    load_fixture,         # cached JSON loader from <pkg>/data/<file>
    error_envelope,       # build {"error": ..., "message": ...}
)
```

Plus convenience envelope shorthands (`from civic_ai_mcp.envelope import not_found, invalid_input, internal_error`).

---

## Test coverage

```
19 passed in ~2s
```

Hermetic — no MCP transport, no network, no LLM. Covers:

- 6 envelope tests (basic, extras, empty-message handling, shorthands, internal_error with exception info)
- 2 logging tests (logger setup, structured-line emission)
- 5 `@traced` tests (success pass-through, exception → envelope, metadata preservation, log shape on ok + error)
- 3 fixture-loader tests (caching, force-reload, missing-file raises loudly)
- 2 server-factory tests (FastMCP instance, env-port respected)
- 1 end-to-end CLI scaffolder test (subprocess `civic-ai-mcp init`, asserts the generated layout is correct)

---

## Part of an MCP-server portfolio

civic-ai-mcp-toolkit is the foundation under six production MCPs. Same architectural shape, six different domains:

- **[gitlaw-mcp](https://github.com/mikelninh/gitlaw)** — German federal law (5,942 statutes), anti-hallucination citation verification, live drift detection
- **[safevoice-mcp](https://github.com/mikelninh/safevoice/tree/main/safevoice_mcp)** — Digital-harassment victim tooling (DE/AT/CH/UK)
- **[grailsense](https://github.com/mikelninh/grailsense)** — NFT collector intelligence over Blockscout
- **[judge-mcp](https://github.com/mikelninh/judge-mcp)** — Domain-agnostic judge + iterate engine (MCP-for-MCPs)
- **[pmm-mcp](https://github.com/mikelninh/pmm-mcp)** — Public Money Mirror: Bundeshaushalt + Bundesrechnungshof
- **[elterngeld-mcp](https://github.com/mikelninh/elterngeld-mcp)** — German parental-benefit calculator + Elterngeldstelle lookup

Future MCPs in the portfolio will use this toolkit from day one rather than copy-paste.

---

## Roadmap

- [ ] **Migrate the six existing MCPs to use civic-ai-mcp-toolkit** (incremental, behind compatibility, one PR per server)
- [ ] **Eval-harness sub-package** — extract the gitlaw-mcp `eval/run.py` pattern as a reusable harness for any MCP
- [ ] **Freshness-pattern sub-package** — extract the gitlaw-mcp `freshness/` scaffold (manifest + drift detection) as a reusable trust layer
- [ ] **TRUST.md template generator** — `civic-ai-mcp trust init` scaffolds an honest trust-statement document
- [ ] **Cross-MCP composition examples** — show how `judge-mcp` can score outputs from `gitlaw-mcp` etc. (the MCP-on-MCP pattern, made discoverable)

---

## License

MIT. Built by extracting the shared shape from six MCP servers in the [civic-AI portfolio](https://github.com/mikelninh). The toolkit and the servers are all MIT — fork, compose, contribute, ship your own.
