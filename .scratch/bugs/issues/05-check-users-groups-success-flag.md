# check_users_belong_to_existing_groups always returns success=True

Status: ready-for-agent
Priority: high
File: `models.py:659`

The `success` flag is never set to `False` even when validation failures are found. Any caller checking the return value silently ignores real errors. `validate()` works around this by inspecting the failures list directly, but the API contract is broken.

## Acceptance criteria

- [ ] Set `success = False` when a failure is appended at `models.py:659`
- [ ] Add a test: user in a non-existent group → `check_users_belong_to_existing_groups` returns `(False, [...])`
