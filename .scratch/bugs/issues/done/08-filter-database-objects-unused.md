# filter_database_objects is defined but never applied

Status: done
Priority: low
File: `admin.py:343`

Stored on the trainer but not used in any `prepare_*` method. Either wire it in or remove it.

## Acceptance criteria

- [ ] Wire `filter_database_objects` into the relevant `prepare_*` methods, or
- [ ] Remove the attribute and its constructor parameter if it has no intended use

## Resolution

Closed via GitHub issue #15, merged in PR #69.
