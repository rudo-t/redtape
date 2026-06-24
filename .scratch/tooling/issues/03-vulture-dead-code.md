# Add vulture for dead code detection

Status: needs-triage

`filter_database_objects` was defined, stored on the trainer, and never called — vulture would have caught it. Run at 80% confidence to avoid noise from `OperationDispatch` dynamic dispatch.

## Work breakdown

- [ ] Add `vulture` to dev dependencies
- [ ] Add to `.pre-commit-config.yaml`:
  ```yaml
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.11
    hooks:
      - id: vulture
        args: [redtape/, --min-confidence, "80"]
  ```
- [ ] Create a `whitelist.py` for any false positives (e.g. `OperationDispatch.register` callbacks)
