"""Vulture whitelist for legitimate false positives.

Vulture cannot follow dynamic dispatch. Names referenced here are flagged as
"unused" by static analysis but are actually invoked at runtime. Listing them
suppresses those false positives.

Run with:
    vulture redtape/ whitelist.py --min-confidence 80
"""

# Query-builder handlers are registered on an ``OperationDispatch`` instance via
# the ``@build_query.register(Operation.X)`` decorator and invoked dynamically
# through ``OperationDispatch.__call__`` keyed by ``Operation``. Vulture sees no
# direct callers, so it reports them as unused.
build_create_query = None
build_drop_query = None
build_grant_query = None
build_group_queries = None
build_ownership_query = None
