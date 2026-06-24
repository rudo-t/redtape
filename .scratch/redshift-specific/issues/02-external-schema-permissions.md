# External schema permissions (Redshift Spectrum / Lake Formation)

Status: needs-triage

External schemas backed by Glue/Lake Formation use a different ACL model than internal schemas. `GRANT USAGE ON SCHEMA` works but Lake Formation column-level security is entirely separate.

## Work breakdown

- [ ] Identify which privileges apply to external schemas (`USAGE`, `CREATE` — no `ALL`)
- [ ] Add `EXTERNAL` flag or separate `ExternalSchema` object type
- [ ] Document the Lake Formation boundary (redtape cannot manage Lake Formation policies)
- [ ] Add integration test (requires a Redshift cluster with a Glue catalog — mark skip)
