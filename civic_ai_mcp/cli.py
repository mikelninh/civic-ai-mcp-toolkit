"""
`civic-ai-mcp init <name>` — scaffold a new MCP project that already follows
the portfolio conventions. Saves the user the copy-paste boilerplate from
existing servers.

Usage:
    civic-ai-mcp init my-cool-mcp
    civic-ai-mcp init my-cool-mcp --port 8010 --description "Does cool things"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _render(template_name: str, **vars: str) -> str:
    raw = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    for k, v in vars.items():
        raw = raw.replace("{{" + k + "}}", v)
    return raw


def _scaffold(target_dir: Path, name: str, description: str, port: int, author: str) -> None:
    """Write the standard project layout."""
    pkg = name.replace("-", "_") + "_mcp"
    name_safe = name.replace("_", "-")

    target_dir.mkdir(parents=True, exist_ok=True)
    pkg_dir = target_dir / pkg
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "data").mkdir(exist_ok=True)
    (target_dir / "tests").mkdir(exist_ok=True)

    # __init__.py
    (pkg_dir / "__init__.py").write_text(
        f'"""{name_safe} MCP — {description}"""\n\n__version__ = "0.1.0"\n',
        encoding="utf-8",
    )

    # server.py
    (pkg_dir / "server.py").write_text(
        _render("server.py.template", name=name_safe, description=description, port=str(port)),
        encoding="utf-8",
    )

    # pyproject.toml
    (target_dir / "pyproject.toml").write_text(
        _render(
            "pyproject.toml.template",
            name=name_safe,
            description=description,
            author=author,
        ),
        encoding="utf-8",
    )

    # tests __init__
    (target_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")

    # basic test
    (target_dir / "tests" / f"test_{pkg}.py").write_text(
        f'''"""Smoke tests for {name_safe}-mcp."""

from {pkg}.server import hello


def test_hello_default():
    result = hello()
    assert result["greeting"] == "Hello, world!"


def test_hello_named():
    result = hello("Mikel")
    assert "Mikel" in result["greeting"]


def test_hello_invalid_input_returns_envelope():
    result = hello(123)  # type: ignore[arg-type]
    assert result.get("error") == "invalid_input"
''',
        encoding="utf-8",
    )

    # README stub
    (target_dir / "README.md").write_text(
        f"""# {name_safe}-mcp

{description}

Built with [civic-ai-mcp-toolkit](https://github.com/mikelninh/civic-ai-mcp-toolkit).

## Install

```bash
pip install -e .
```

Add to your Claude Desktop config:

```json
{{
  "mcpServers": {{
    "{name_safe}": {{
      "command": "{name_safe}-mcp"
    }}
  }}
}}
```

## Test

```bash
pytest
```

## License

MIT.
""",
        encoding="utf-8",
    )

    # gitignore
    (target_dir / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n*.egg-info/\n.venv/\n.pytest_cache/\n.DS_Store\n.env\n.env.*\ndist/\nbuild/\n",
        encoding="utf-8",
    )

    # MIT LICENSE
    (target_dir / "LICENSE").write_text(
        f"MIT License\n\nCopyright (c) 2026 {author}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="civic-ai-mcp")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="Scaffold a new MCP server with portfolio conventions")
    init.add_argument("name", help="short name, e.g. 'flight-rights' (becomes flight-rights-mcp)")
    init.add_argument("--description", default="A Model Context Protocol server.")
    init.add_argument("--port", type=int, default=8010)
    init.add_argument("--author", default=os.getenv("USER", "anon"))
    init.add_argument("--target", default=None, help="target directory (default: ./<name>-mcp)")

    args = parser.parse_args()

    if args.cmd == "init":
        target = Path(args.target or f"./{args.name}-mcp")
        if target.exists() and any(target.iterdir()):
            print(f"error: {target} already exists and is non-empty", file=sys.stderr)
            return 2
        _scaffold(target, args.name, args.description, args.port, args.author)
        print(f"scaffolded {target}")
        print(f"  next: cd {target} && pip install -e . && pytest")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
