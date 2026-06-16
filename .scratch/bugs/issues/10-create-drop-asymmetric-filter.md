# CREATE vs DROP use inconsistent sides of the group/user filter

Status: needs-triage
Priority: low
Files: `admin.py:436–444`

`prepare_create_subjects` uses the filtered desired list and unfiltered current list; `prepare_drop_subjects` is the inverse. Filter behaviour for CREATE and DROP is asymmetric.

## Acceptance criteria

- [ ] Audit both methods and apply the filter consistently on the same side
- [ ] Add tests that verify filter behaviour is symmetric for CREATE and DROP
