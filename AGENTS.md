# WinstyleS

WinstyleS manages portable Windows personalization profiles through a Python
plugin engine, CLI, and local browser UI.

Use a Windows-owned Python environment; keep Windows and WSL environments separate.
Dependencies and formatter settings live in `pyproject.toml`.

- **Develop or verify:** read [CONTRIBUTING.md](CONTRIBUTING.md) for setup and checks.
- **Change import, packages, or Web API:** read [behavior](docs/behavior.md) for
  safety boundaries and compatibility expectations, then run its regression tests.
- **Find extension points:** read [architecture](docs/ARCHITECTURE.md).
- **Choose product scope or UI direction:** read [modernization](docs/modernization.md).

Use fixtures and temporary directories for write-path tests. Real system apply,
publishing, and configuration uploads require explicit user authorization.
