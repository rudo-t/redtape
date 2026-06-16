# Harden mypy configuration

Status: needs-triage

mypy is in dev dependencies but its config is minimal and it is not in pre-commit.

## Work breakdown

- [ ] Enable the attrs mypy plugin (gives proper type inference through `@attrs.define`):
  ```toml
  [tool.mypy]
  python_version = "3.10"
  plugins = ["mypy.plugins.attrs"]
  strict = true
  ignore_missing_imports = true
  ```
- [ ] Add mypy to `.pre-commit-config.yaml` (see issue #04)
- [ ] Resolve any new type errors surfaced by `strict = true`
