# Make ownership management opt-in so default `run` never requires superuser

Status: needs-triage
Issue: #67

`ALTER ... OWNER TO` is the only operation redtape emits that requires cluster superuser on Redshift. Ownership is currently opt-*out* (`filter_operations` defaults to `no_filter`), so any spec with an `owns:` block makes a plain `redtape run` attempt superuser-only statements — the safe path is the non-default path.

## Proposal

Flip to opt-in: `DatabaseAdministratorTrainer` defaults to `manage_ownership: bool = False` (skips `prepare_alter_ownership` entirely), and `run` gains an explicit `--manage-ownership` flag that must be passed for `ALTER_OWNER` to be emitted.

## Work breakdown

- [ ] Engine: default ownership off; keep `filter_operations` truthiness-safe (issue #16)
- [ ] CLI: add `--manage-ownership`; define interaction with `--operation`
- [ ] Warn (not silent no-op) when a spec declares `owns:` but ownership management is off
- [ ] Tests: default run with `owns:` emits zero `ALTER_OWNER`; `--manage-ownership` emits them; warning fires
- [ ] Docs: README Ownership section — CI (default, non-superuser) vs operator (opt-in, privileged) split

## Notes

Behavioural change: specs relying on default `run` applying `owns:` stop doing so until `--manage-ownership` is passed. Call out in changelog + runtime warning. Relates to #26 (done) and supersedes #66 for the superuser concern specifically.
