# Unit test gaps — specification/models.py and __init__.py (89% / 98% coverage)

Status: ready-for-agent

Uncovered lines from coverage report. All tests go in `tests/test_specification.py`.

## models.py gaps

**FUNCTION / PROCEDURE / LANGUAGE supported actions** (`models.py:90–96`)
- `DatabaseObject("fn", FUNCTION).is_action_supported(Action.EXECUTE)` → True
- `DatabaseObject("fn", FUNCTION).is_action_supported(Action.SELECT)` → False
- Same pair for PROCEDURE and LANGUAGE

**`Privilege.validate()` with `action=None`** (`models.py:200`)
- `Privilege(database_object=..., action=None).validate()` → `(True, None)`

**`Operation.canonical` property** (`models.py:229–232`)
- `Operation.ALTER_OWNER.canonical == "ALTER"`
- `Operation.CREATE.canonical == "CREATE"` (else branch)
- `Operation.GRANT.canonical == "GRANT"`

**`Password.__str__` SHA256 with salt** (`models.py:273`)
- `str(Password(SHA256, "deadbeef", salt="abc"))` — documents the broken output; update assertion after bug #03 is fixed

**`Group.__eq__` comparisons** (`models.py:342, 346`)
- `Group("analysts") == "analysts"` → True
- `Group("analysts") == 42` → `NotImplemented`

**`Group.__repr__`** (`models.py:349`)
- `repr(Group("analysts"))` → contains `"analysts"`

**`User.__eq__` unknown type** (`models.py:397, 413`)
- `User("alice", False) == 42` → `NotImplemented`

**`User.__repr__`** (`models.py:416`)
- `repr(User("alice", False))` → contains `"alice"`

**`User.validate()` full success path** (`models.py:452`)
- `User("alice", False, privileges=Privileges([valid_priv]), password=Password(PLAIN, "Secret123!"))` → `(True, None)`

**`Specification.group_to_users()`** (`models.py:587–592`)
- Spec with a group and two users where one is a member → `list(spec.group_to_users())` returns group paired with only the member

**`Specification.user_to_groups()`** (`models.py:596–608`)
- User with `member_of=None` → skipped
- Spec with `groups=None` → users paired with `[]`

## specification/__init__.py gaps

**Password with salt serialised** (`__init__.py:110`)
- `Password(SHA256, "abc", salt="xyz")` serialised via `to_dict()` → dict contains `"salt": "xyz"`

**Generic Enum serialiser fallback** (`__init__.py:117`)
- Identify which model field (if any) triggers the generic Enum serialiser during `asdict()` and add a targeted test
