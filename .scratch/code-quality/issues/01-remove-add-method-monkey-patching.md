# Replace add_method monkey-patching with explicit methods or a mixin

Status: needs-triage
File: `specification/__init__.py:122`

`add_method` patches `to_yaml`, `from_json`, etc. onto `Specification`, `User`, and `Group` at module import time. IDEs and type checkers cannot see these methods, so autocomplete and mypy are blind to them.

## Acceptance criteria

- [ ] Replace `add_method` calls with either: explicit method definitions on each class, or a `SerialisableMixin` that `Specification`, `User`, and `Group` inherit from
- [ ] All existing serialisation tests continue to pass
- [ ] mypy can resolve `spec.to_yaml()` without `# type: ignore`
