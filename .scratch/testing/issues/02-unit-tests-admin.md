# Unit test gaps — admin.py (84% coverage)

Status: ready-for-agent

Uncovered lines from coverage report. All tests go in `tests/test_admin.py`.

## Missing tests

**String representations** (`admin.py:113–121, 124, 159–167, 170`)
- `str(UserManagementOperation(GRANT, user, privilege))` → contains `"GRANT"` and `"to"`
- `str(UserManagementOperation(REVOKE, user, privilege))` → contains `"REVOKE"` and `"from"`
- `str(UserManagementOperation(CREATE, user))` → privilege is None path
- `str(UserManagementOperation(ADD_TO_GROUP, user, group=group))` → group path, contains `"to"`
- `str(UserManagementOperation(DROP_FROM_GROUP, user, group=group))` → group path, contains `"from"`
- `repr(UserManagementOperation(...))` → non-empty string, no crash
- `repr(GroupManagementOperation(...))` → mark `xfail` until bug #07 is fixed

**`ManagementOperation.query` caching property** (`admin.py:132–134`)
- Call `op.query` twice; assert `op._query is not None` after first access

**`ManagementOperationError`** (`admin.py:79–81`)
- `ManagementOperationError(op)` → `op in str(err)`

**`prepare_subjects` invalid operation** (`admin.py:470`)
- `trainer.prepare_subjects(users, users, Operation.GRANT)` → `TypeError`

**GRANT when subject already exists in current spec** (`admin.py:560`)
- Desired group has privilege X; current has same group with privilege Y → GRANT X only (hits the `else` branch that reads `current_privileges = self.current.groups[idx].privileges`)

**REVOKE when subject already exists in desired spec** (`admin.py:602`)
- Current group has privilege X; desired group exists with privilege Y → REVOKE X

**`_do_nothing`** (`admin.py:694`)
- `_do_nothing("a", "b", key="c")` → no exception

**`DatabaseAdministrator.queries()`** (`admin.py:710–711`)
- `list(admin.queries())` with one op → one `(str, ManagementOperation)` tuple

**`DatabaseAdministrator.manage()` — mock connector** (`admin.py:748–777`)
- Happy path → `(True, [])`, callbacks called
- `OnError.CONTINUE` with psycopg2.Error → `success=False`, error appended, execution continues
- `OnError.ABORT` with psycopg2.Error → `ManagementOperationError` raised
- `before_callback` return value passed through to `success_callback`
- Empty ops list → `(True, [])` without touching connector
