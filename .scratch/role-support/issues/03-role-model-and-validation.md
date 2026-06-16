# Role model + spec validation

Status: ready-for-agent

Add the `Role` model and wire it into the spec so `redtape validate` passes on a spec that includes roles.

## What to build

- Add a `Role` attrs model to `specification/models.py` (name, member_of, privileges) following the same pattern as `Group`
- Add `Specification.roles: list[Role]`
- Update `Specification.__attrs_post_init__` to handle `roles=None`
- Update the cattrs converter to serialise/deserialise roles in YAML
- Rename `member_of` → `groups` on `User` (breaking change per issue 02) and add `roles: list[str]` field to `User`
- Update `Specification.validate()` to check that role names referenced in `users.roles` and `roles.member_of` exist in `Specification.roles`
- Update YAML round-trip tests

## Acceptance criteria

- [ ] `redtape validate spec.yml` passes on a spec with roles, role-to-role membership, and users with `roles:`
- [ ] `redtape validate spec.yml` fails if a user references a role not declared in `roles:`
- [ ] Existing spec files using `member_of:` on users fail validation with a clear migration message
- [ ] YAML round-trip: spec → `to_yaml()` → `from_yaml()` preserves all role data
- [ ] `schema_names` is still excluded from serialised output

## Blocked by

`.scratch/role-support/issues/02-role-spec-format.md`
