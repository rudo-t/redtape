# `!include` directive for splitting specs across files

Status: needs-triage

Large organisations will outgrow a single spec file quickly. An `!include` directive lets teams own their own slice of the spec.

## Design

Pre-process the top-level YAML before passing to `Specification.from_yaml`. Two options:
1. Custom YAML loader that resolves `!include path/to/fragment.yml` tags before parsing
2. A `merge_yaml_files([path1, path2])` helper called explicitly (simpler, no custom loader)

Option 2 is recommended for an MVP — avoids YAML loader complexity.

## Acceptance criteria

- [ ] `Specification.from_yaml_files([path1, path2])` merges `users` and `groups` lists before deserialising
- [ ] Duplicate user/group names across files raise a `ValueError` with a clear message
- [ ] Add unit tests for merge, duplicate detection, and file-not-found
