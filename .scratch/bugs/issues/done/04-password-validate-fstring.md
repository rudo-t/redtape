# Password.validate() error message never interpolates

Status: done
Priority: critical
File: `models.py:282`

`"Password must be between 8 and 64 characters, not {len(self.value)}"` is missing the `f` prefix. Error messages always show the literal string `{len(self.value)}` rather than the actual length.

## Acceptance criteria

- [ ] Add `f` prefix to the string literal at `models.py:282`
- [ ] Add a test that asserts the error message contains the actual integer length

## Resolution

Closed via GitHub issue #11, merged in PR #48.
