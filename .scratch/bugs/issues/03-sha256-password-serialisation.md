# SHA256 password serialisation broken — missing f-string prefix

Status: ready-for-agent
Priority: critical
File: `models.py:265`

The salt branch uses a plain string `"|{self.salt}"` instead of an f-string, so the literal text `{self.salt}` is written to the database rather than the actual salt value.

## Acceptance criteria

- [ ] Change `"|{self.salt}"` to `f"|{self.salt}"`
- [ ] Add a test: `str(Password(SHA256, "deadbeef", salt="abc"))` ends with `"|abc"`, not `"|{self.salt}"`
