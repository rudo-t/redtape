# filter_operations uses strict `is True` identity check

Status: ready-for-agent
Priority: low
File: `admin.py:397`

Any truthy non-`True` return from a filter callback (e.g. `1`, a non-empty string) silently skips the operation. Should use a truthiness check (`if not result:`) rather than `if result is not True:`.

## Acceptance criteria

- [ ] Change the identity check to a truthiness check
- [ ] Add a test: filter that returns `1` (truthy non-True) — operation should be included, not skipped
