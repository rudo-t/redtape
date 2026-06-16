# `build_grant_query` raises NameError instead of TypeError

Status: done
Priority: critical
Files: `admin.py:196`, `admin.py:272`

Both `UserManagementOperation` and `GroupManagementOperation` reference bare `operation` and `privilege` in the error branch — neither name is in scope at that point. Creating a GRANT op with `privilege=None` raises `NameError` instead of the intended `TypeError`. Should be `self.operation` / `self.privilege`.

## Acceptance criteria

- [x] Fix both occurrences: `admin.py:196` and `admin.py:272`
- [x] Add a test: `UserManagementOperation(GRANT, user, privilege=None)` → `TypeError`
- [x] Add a test: `GroupManagementOperation(GRANT, group, privilege=None)` → `TypeError`

## Resolution

Replaced bare `operation` / `privilege` with `self.operation` / `self.privilege` in
both `build_grant_query` methods. Added `test_user_management_operation_grant_without_privilege_raises_typeerror`
and `test_group_management_operation_grant_without_privilege_raises_typeerror` to
`tests/test_admin.py`. Full unit suite: 87 passed.
