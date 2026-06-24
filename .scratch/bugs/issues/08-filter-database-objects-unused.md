# filter_database_objects is defined but never applied

Status: needs-triage
Priority: low
File: `admin.py:343`

Stored on the trainer but not used in any `prepare_*` method. Either wire it in or remove it.

## Acceptance criteria

- [ ] Wire `filter_database_objects` into the relevant `prepare_*` methods, or
- [ ] Remove the attribute and its constructor parameter if it has no intended use
