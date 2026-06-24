# Code quality toolchain: ruff, strict mypy (ratcheted), vulture

Linting and formatting are consolidated into **ruff** (replacing black + isort + flake8), type checking uses **mypy** in `strict` mode, and dead-code detection uses **vulture**. All three are configured in `pyproject.toml` and run via `uv run --with <tool>`. See `AGENTS.md` for the exact commands and conventions.

We considered keeping the three-tool lint stack and turning strict typing on only after the codebase fully passed it. Both were rejected:

- ruff subsumes all three linters, is configured in one place, and its `F821` (undefined name) / `F401` (unused import) rules catch the class of latent `NameError` bugs that had already shipped (e.g. an undefined `idx` in `cli.py`).
- Requiring a fully strict-clean tree before enabling `strict = true` would have meant either a large risky rewrite or leaving strict off indefinitely. Instead we **ratchet**: `strict = true` is on, and the ~230 pre-existing errors are parked in a documented `disable_error_code` list in `[tool.mypy]`. New code is held to strict; deferred codes are cleared as the relevant modules are touched.

Two interactions with existing design are load-bearing and should not be "fixed" casually:

- The `@build_query.register(...)` handlers are reached through `OperationDispatch` dynamic dispatch, so static tools cannot see them used. They are recorded in `whitelist.py` for vulture rather than deleted, and they are the source of much of the deferred mypy/pyright noise. This is the same monkey-patching tracked by issue #20 — resolving #20 would let several deferred error codes be removed.
- The attrs mypy plugin entry point `mypy.plugins.attrs` is **invalid** and breaks mypy on startup; attrs support is built into mypy's default plugin, so no `plugins` entry is configured.

Wiring these tools into `.pre-commit-config.yaml` is deferred to issue #45; the integration tests under `tests/integration/` require a live cluster (issue #38) and are excluded from the must-pass unit run.
