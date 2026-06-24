# Remove poetry — standardise on pyproject.toml + uv

Status: done
Priority: highest (do this before any other tooling work)

The repo has both a `[project]` table (PEP 621, used by uv and pip) and a `[tool.poetry]` section. The build backend was `poetry-core` and has been switched to `hatchling`. `poetry.lock` is stale. Clean up the leftovers so there is one clear way to install and build the project.

## What to do

- [x] Remove the `[tool.poetry]` and `[tool.poetry.dependencies]` and `[tool.poetry.dev-dependencies]` sections from `pyproject.toml` — the `[project]` table supersedes them
- [x] Delete `poetry.lock`
- [x] Run `uv lock` to regenerate `uv.lock` from the current `[project]` dependencies
- [x] Verify `uv sync --group dev` installs everything and `pytest tests/ -v --ignore=tests/integration` passes
- [x] Verify `pip install -e ".[dev]"` also works (used by ralph inside Docker)
- [x] Update `README.md` install instructions: replace `poetry install` with `uv sync --group dev`

## Acceptance criteria

- [x] `pyproject.toml` has no `[tool.poetry*]` sections
- [x] `poetry.lock` is deleted
- [x] `uv.lock` is up to date (committed)
- [x] `uv sync --group dev && pytest tests/ -v --ignore=tests/integration` passes with 0 failures
- [x] `pip install -e ".[dev]" && pytest tests/ -v --ignore=tests/integration` passes with 0 failures

## Blocked by

None — can start immediately.

## Resolution

- Removed `[tool.poetry]`, `[tool.poetry.dependencies]`, `[tool.poetry.dev-dependencies]` from `pyproject.toml`.
- Deleted `poetry.lock` (git rm); regenerated `uv.lock` via `uv lock`.
- **Decision:** `pip install -e ".[dev]"` reads `[project.optional-dependencies]`,
  not the PEP 735 `[dependency-groups]` table. Added a mirrored `dev` extra under
  `[project.optional-dependencies]` so both the ralph feedback loop (`pip install
  -e '.[dev]'`) and `uv sync --group dev` work. The two dev lists are kept in sync
  by hand.
- Verified `pip install -e ".[dev]"` in a clean Python 3.12 venv (matching ralph's
  `python:3.12-slim`) — note: requires-python is `>=3.12`, so the host's default
  3.9 interpreter cannot install it. Tests: 87 passed under both uv and pip envs.
