# HITL: Agree on role spec YAML format

Status: ready-for-human

The YAML format for roles must be decided before any code is written. This slice is the blocker for all other role support work.

## What to build

Agree on and document the spec format for Redshift RBAC roles. No code changes — output is a written decision that unblocks slices 03–06.

## Agreed format

```yaml
roles:
  - name: analytics_role
    member_of:
      - reporting_role     # GRANT ROLE reporting_role TO ROLE analytics_role
    privileges:
      table:
        select:
          - raw.public.orders

users:
  - name: alice
    is_superuser: false
    groups:                # breaking change: replaces member_of for legacy groups
      - my_group
    roles:
      - analytics_role     # GRANT ROLE analytics_role TO USER alice
```

## Key decisions recorded here

- `member_of` on a role = role-to-role inheritance (upward, consistent with permifrost convention)
- `groups:` replaces `member_of:` on users for legacy group membership — **breaking change** to all existing spec files
- `roles:` on users = RBAC role membership (new field)
- Privileges on roles use raw SQL actions (select, insert, etc.), not read/write shorthand — shorthand is a separate feature

## Acceptance criteria

- [ ] This format is confirmed as the canonical spec shape
- [ ] Breaking change (`member_of` → `groups` on users) is documented in a changelog or migration note
- [ ] Slices 03–06 can proceed

## Blocked by

None — can start immediately.
