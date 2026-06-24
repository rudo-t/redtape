# Add `read` / `write` privilege shorthand to the spec format

Status: needs-triage

Requiring users to specify raw Postgres action names (`select`, `insert`, etc.) is a UX barrier. Permifrost maps `read` → `{SELECT}` on tables / `{USAGE}` on schemas. Redtape should offer a similar optional abstraction.

## Proposed expansion rules

| Shorthand | Object type | Expands to |
|---|---|---|
| `read` | TABLE / VIEW | `SELECT` |
| `read` | SCHEMA | `USAGE` |
| `read` | DATABASE | `CONNECT` |
| `write` | TABLE | `SELECT, INSERT, UPDATE, DELETE` |
| `write` | SCHEMA | `USAGE, CREATE` |

## Work breakdown

- [ ] Define expansion mapping in `specification/models.py`
- [ ] Apply expansion as a pre-processing step before diffing (not stored in the model)
- [ ] Update YAML spec documentation
- [ ] Add unit tests for each expansion case per object type
