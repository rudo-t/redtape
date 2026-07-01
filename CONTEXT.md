# redtape

A CLI tool for declarative privilege management on Amazon Redshift. Reads a spec describing the desired state of grantees and their privileges; diffs against the actual state in the live database; and emits SQL to close the gap. (Postgres support is planned — see issue #27 — but only Redshift is implemented today.)

## Scope (MVP)

MVP manages **users, groups, and privileges**, and includes applying changes to a live cluster (a real `run`, not only `--dry`). Explicitly **post-MVP**: RBAC **roles** (#32 epic) and **Postgres** support (#27).

MVP issues: #9, #15, #17 done; #26 (PR #65) and #38 (PR #68) in review. #18 (atomic rollback) was reclassified post-MVP — it is hardening, not viability: since #9 the whole plan already applies over one connection that rolls back on error, so `--atomic` (PR #64) only adds a clean abort-on-first-error.

## Language

### Core workflow

**Spec**:
The YAML file that declares the desired state of grantees and their privileges. Short form of "spec file." The in-memory representation is an implementation detail (`Specification` class).
_Avoid_: specification file, config file, permissions file

**Desired spec**:
The YAML-declared target state — what privileges grantees should have after a run.
_Avoid_: wanted, expected, target spec, current spec

**Actual spec**:
The live-database state — what privileges grantees currently have, loaded from the database at run time.
_Avoid_: current spec, present spec, existing spec

**Plan**:
The ordered list of operations computed by diffing the desired spec against the actual spec. Printed by a dry run; executed by run.
_Avoid_: diff, changeset, operations list

**Run**:
The act of executing a plan against the live database — computing the diff between the desired spec and actual spec, then running each operation. Invoked via `redtape run`.
_Avoid_: apply, execute, deploy

**Dry run**:
A run that prints the plan without executing any operations against the database. Invoked via `redtape run --dry`.
_Avoid_: preview, simulate, what-if

**Export**:
Reading the live database state and writing it as a spec file. Invoked via `redtape export`. The output becomes the starting point for a desired spec.
_Avoid_: snapshot, capture, dump, introspect

### Operations

**Operation**:
A single SQL statement within a plan — e.g. `GRANT SELECT ON my_table TO alice` or `CREATE USER bob`.
_Avoid_: statement, step, command, action

**Operation type**:
The classifier of an operation: GRANT, REVOKE, CREATE, DROP, ADD_TO_GROUP, DROP_FROM_GROUP, ALTER_OWNER.
_Avoid_: operation kind, operation mode, verb

**Transaction**:
The unit of atomicity for a run. Since #9 the whole plan runs over a single connection that commits on success and rolls back if an operation raises. The `--atomic` flag (`OnError.ABORT`, PR #64) makes a run stop at the first failing operation and roll back the whole plan; the default (`OnError.CONTINUE`) reports the error and carries on. Note that on Redshift a failed statement aborts the session transaction, so a continued run's later statements also fail until the transaction ends.
_Avoid_: batch, unit of work

### Privileges

**Privilege**:
A specific right granted to a grantee on a database object — e.g. `SELECT ON my_schema.my_table`. The atomic unit redtape manages.
_Avoid_: permission, access, right

**Action**:
The SQL verb within a privilege — SELECT, INSERT, UPDATE, DELETE, USAGE, EXECUTE, etc.
_Avoid_: privilege (for this concept), permission, right

**Database object**:
The target of a privilege — a table, schema, database, function, procedure, or language. The thing you grant access *to*.
_Avoid_: resource, target, object

### Grantees

**Grantee**:
A user, group, or role — anything that can be granted or revoked a privilege.
_Avoid_: subject, entity, principal

**Group**:
A legacy Redshift security group, created with `CREATE GROUP`. Distinct from a role.
_Avoid_: role (for this concept)

**Role**:
A Redshift RBAC role, created with `CREATE ROLE` (available since 2022). Supports role-to-role inheritance via `member_of`. Distinct from a group.
_Avoid_: group (for this concept)

## Glossary vs. code

The code has not yet caught up to this glossary in two places — expect the drift when navigating:

- **Actual spec** is called `current` in code (`current_spec`, `self.current`, `current_users`, …). Rename to `actual` tracked by issue #23.
- **Grantee** is called `subject` in code (`UserManagementOperation.subject`, the `prepare_subjects` methods). No rename issue filed yet.
