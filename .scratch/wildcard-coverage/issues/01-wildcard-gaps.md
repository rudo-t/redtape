# Wildcard coverage gaps

Status: needs-triage

Three remaining gaps after `feat/schema-wildcard` landed schema-level expansion.

## Work breakdown

- [ ] **Database-level wildcard** — `*` in the database position (e.g. `*.*` for all schemas across all databases) is not supported in the spec format
- [ ] **Function / procedure wildcards** — `db.schema.*` for FUNCTION and PROCEDURE object types
- [ ] **Warning when wildcards can't expand** — `_expand_schema_wildcards` silently passes through unexpanded wildcards when `schema_names` is empty (i.e. both specs are YAML-loaded rather than loaded from a connector). Add a warning log or validation failure in this case

## Acceptance criteria

- [ ] All three wildcard forms expand correctly in the diff engine
- [ ] Unit tests cover expansion for each object type
- [ ] A warning (or validation failure) is emitted when a wildcard is present but `schema_names` is empty
