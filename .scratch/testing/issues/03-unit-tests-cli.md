# Unit test gaps — cli.py (45% coverage)

Status: ready-for-agent

Uncovered lines from coverage report. All tests go in `tests/test_cli.py`. Tests that touch `RedshiftConnector` patch it with `unittest.mock.patch("redtape.cli.RedshiftConnector")`.

## Missing tests

**`run --dry`** (`cli.py:195–201`)
- Mock connector; assert exit 0 and `"GRANT"` in output

**`run` — nothing to do** (`cli.py:205–207`)
- Mock connector returns current spec identical to desired → no ops → exit 1

**`run --skip-validate`** (`cli.py:155–159`)
- Spec that would fail validation (user in missing group) → with `--skip-validate` proceeds past validation

**`run --user filter`** (`cli.py:175–180`)
- Spec with two users; `--user alice` → only alice's operations in dry-run output

**`run --group filter`** (`cli.py:182–187`)
- Same pattern for `--group`

**`run --operation filter`** (`cli.py:189–190`)
- `--operation grant` → no REVOKE in output

**`export` — YAML output** (`cli.py:95–112`)
- Mock connector; assert exit 0 and `"users:"` in output

**`export --json`**
- Mock connector; assert `"users"` key in parsed JSON output

**`load_spec` — stdin path** (`cli.py:278–280`)
- `runner.invoke(app, ["validate"], input=yaml_string)` — no file argument

**`load_spec` — ValueError branch** (`cli.py:299–301`)
- Syntactically valid YAML with unknown enum value → exit 1

**`load_spec` — ConnectionError branch** (`cli.py:302–304`)
- Mock connector raises `ConnectionError` → exit 1
