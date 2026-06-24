# redtape

A CLI tool for declarative privilege management on Redshift and Postgres. Reads a spec describing the desired state of grantees and their privileges; diffs against the actual state in the live database; and emits SQL to close the gap.

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
