# GroupManagementOperation.__repr__ crashes with AttributeError

Status: ready-for-agent
Priority: high
File: `admin.py:254`

`__repr__` references `self.group`, which does not exist as an attribute on `GroupManagementOperation`. Any call to `repr()` on a group operation raises `AttributeError`.

## Acceptance criteria

- [ ] Fix `__repr__` to reference the correct attribute
- [ ] Add a test (currently marked `xfail`) that calls `repr(GroupManagementOperation(...))` without crashing
