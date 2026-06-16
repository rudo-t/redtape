# User.validate() skips password check when privileges is None

Status: needs-triage
Priority: high
File: `models.py:431`

Early return before the password validation block. A user with `privileges=None` and a weak or invalid password passes validation silently.

## Acceptance criteria

- [ ] Move the password validation block before or outside the `privileges is None` early return
- [ ] Add a test: user with `privileges=None` and an invalid password → validation fails
