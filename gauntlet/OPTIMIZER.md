# Civic MCP Gauntlet Optimizer

Apply this contract to one MCP server and one domain at a time.

1. Freeze domain fixtures, source snapshots, gold outputs and edge cases.
2. Run all deterministic checks before any LLM-based judging.
3. Classify failures: calculation/retrieval, schema, tool selection, grounding, error recovery or presentation.
4. State one falsifiable hypothesis.
5. Change one coherent mutable surface only.
6. Rerun the complete suite plus held-out cases.
7. Any schema, structured-error, grounding, tracing or domain-safety regression => `REVERT`.
8. Otherwise `KEEP` only if held-out task success improves while deterministic correctness stays equal or better.
9. Record hypothesis, diff, metrics and decision in Git.

Use `judge-mcp` only for qualities that genuinely require judgement (clarity, usefulness, completeness). Never let it override deterministic legal/calculation/source checks.

The goal is a common eval shape across Elterngeld, public money, flight rights, Wohngeld, AGB and future civic MCPs without erasing their domain-specific hard gates.
