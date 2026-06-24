# Replace black + isort + flake8 with ruff

Status: ready-for-agent

Three separate tools replaced by one. Ruff is maintained by the same team as `uv` (already in use), 10–100× faster, and configured entirely in `pyproject.toml`. The existing `isort` config has stale `py_version = 38` despite the project requiring Python 3.10+.

## Work breakdown

- [ ] Remove `black`, `isort`, `flake8` from dev dependencies in `pyproject.toml`
- [ ] Add `ruff` to dev dependencies
- [ ] Add ruff config to `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 88
  target-version = "py310"

  [tool.ruff.lint]
  select = ["E", "W", "F", "I", "B", "N", "UP", "S", "SIM", "RUF"]
  ignore = ["S101"]

  [tool.ruff.lint.per-file-ignores]
  "tests/*" = ["S", "N"]
  ```
- [ ] Run `ruff check --fix .` and `ruff format .`; resolve any remaining violations
- [ ] Update `.pre-commit-config.yaml` to use `astral-sh/ruff-pre-commit` (see issue #04)

## Notes

The `F821` (undefined name) rule would have caught the `build_grant_query` NameError bug before it was committed.
