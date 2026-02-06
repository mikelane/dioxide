# Migrating from v1.x to v2.0

**Target audience:** Developers upgrading an existing dioxide v1.x project to v2.0.

**Estimated migration time:** 15-30 minutes for most projects.

---

## We hear you

The v2.0 release included a breaking change to the `Profile` class, and we know
that stung. If you had code that relied on `profile.value`, `profile.name`, or
iterating over `Profile`, it broke when you upgraded. That is a real cost, and we
do not take it lightly.

This guide exists because you deserve a clear path forward -- not a dismissive
"just update your code." We will walk through every breaking change, show you
exactly what to change, and give you automated find-replace patterns so the
migration is as painless as possible.

---

## Why v2.0 was necessary

The v1.x `Profile` was a `StrEnum`. That worked well for the built-in profiles
(`PRODUCTION`, `TEST`, `DEVELOPMENT`, `STAGING`, `CI`), but it had a fundamental
limitation: **you could not create custom profiles without modifying the library
itself.**

Real-world projects need profiles like `integration`, `load-test`, `preview`, or
`canary`. With `StrEnum`, adding these required either:

- Forking the library to add new enum members, or
- Using raw strings and losing type safety entirely.

Neither option was acceptable. v2.0 changed `Profile` from a `StrEnum` to an
extensible `str` subclass, which means:

- All built-in profiles (`Profile.PRODUCTION`, `Profile.TEST`, etc.) still work
  exactly the same way.
- You can now define custom profiles that are first-class citizens:

```python
# v2.0: Custom profiles are type-safe and work everywhere
INTEGRATION = Profile('integration')
LOAD_TEST = Profile('load-test')
PREVIEW = Profile('preview')

@adapter.for_(MetricsPort, profile=INTEGRATION)
class DatadogMetrics:
    ...

@adapter.for_(MetricsPort, profile=[LOAD_TEST, PREVIEW])
class MockMetrics:
    ...
```

The tradeoff was breaking three `StrEnum`-specific patterns that a `str` subclass
does not support. We believe the extensibility gain justifies the migration cost,
and this guide is our commitment to making that migration as smooth as possible.

---

## Timeline

| Event | Date |
|-------|------|
| v1.0.0 released | December 2025 |
| v1.1.2 released (last v1.x) | January 2026 |
| v2.0.0 released | January 23, 2026 |
| v1.x end of life | No longer receiving patches |

If you need to stay on v1.x temporarily, pin your dependency:

```
dioxide>=1.0.0,<2.0.0
```

---

## Complete list of breaking changes

v2.0 has exactly **one** category of breaking change: the `Profile` class moved
from `StrEnum` to `str` subclass. Everything else in the API is backward
compatible.

### 1. `profile.value` no longer exists

`StrEnum` members had a `.value` attribute that returned the underlying string.
`str` subclass instances **are** the string, so `.value` is not needed.

:::::{tab-set}

::::{tab-item} Before (v1.x)
```python
# v1.x -- accessing the string value of a profile
profile = Profile.PRODUCTION
print(profile.value)          # 'production'

if adapter_profile.value == "production":
    connect_to_prod()

config = {"profile": profile.value}
```
::::

::::{tab-item} After (v2.0)
```python
# v2.0 -- Profile IS a string, use it directly
profile = Profile.PRODUCTION
print(profile)                # 'production'
print(str(profile))           # 'production' (explicit conversion also works)

if adapter_profile == "production":
    connect_to_prod()

config = {"profile": profile}  # or str(profile) if you need a plain str
```
::::

:::::

### 2. `profile.name` no longer exists

`StrEnum` members had a `.name` attribute that returned the Python identifier
(e.g., `"PRODUCTION"`). The `str` subclass does not have this attribute. In
practice, `.name` was rarely used in application code.

:::::{tab-set}

::::{tab-item} Before (v1.x)
```python
# v1.x -- accessing the enum member name
profile = Profile.PRODUCTION
log.info(f"Active profile: {profile.name}")  # 'PRODUCTION'
```
::::

::::{tab-item} After (v2.0)
```python
# v2.0 -- use the profile string directly or repr()
profile = Profile.PRODUCTION
log.info(f"Active profile: {profile}")       # 'production'
log.info(f"Active profile: {profile!r}")     # "Profile('production')"
```
::::

:::::

### 3. Iterating over `Profile` no longer works

`StrEnum` was iterable (you could loop over all members). A `str` subclass is
not enumerable in the same way. If you need a list of profiles, use an explicit
collection.

:::::{tab-set}

::::{tab-item} Before (v1.x)
```python
# v1.x -- iterating over all profile members
for p in Profile:
    print(p.value)

all_profiles = list(Profile)
```
::::

::::{tab-item} After (v2.0)
```python
# v2.0 -- use an explicit list of the profiles you need
KNOWN_PROFILES = [
    Profile.PRODUCTION,
    Profile.TEST,
    Profile.DEVELOPMENT,
    Profile.STAGING,
    Profile.CI,
]

for p in KNOWN_PROFILES:
    print(p)

# If you also have custom profiles, include them
ALL_MY_PROFILES = KNOWN_PROFILES + [INTEGRATION, LOAD_TEST]
```
::::

:::::

### 4. `Profile['PRODUCTION']` bracket access no longer works

`StrEnum` supported bracket-style member access. The `str` subclass does not.

:::::{tab-set}

::::{tab-item} Before (v1.x)
```python
# v1.x -- bracket access to enum members
profile = Profile['PRODUCTION']
```
::::

::::{tab-item} After (v2.0)
```python
# v2.0 -- use the class attribute directly
profile = Profile.PRODUCTION

# If you need dynamic access from a string, construct a Profile instance
profile = Profile('production')
```
::::

:::::

---

## What did NOT change

Everything else works exactly as it did in v1.x:

- `Profile.PRODUCTION`, `Profile.TEST`, `Profile.DEVELOPMENT`, `Profile.STAGING`,
  `Profile.CI`, `Profile.ALL` -- all still exist as class attributes.
- `Profile.PRODUCTION == 'production'` -- still `True` (Profile is a str subclass).
- `isinstance(Profile.PRODUCTION, str)` -- still `True`.
- `@adapter.for_(Port, profile=Profile.PRODUCTION)` -- unchanged.
- `@adapter.for_(Port, profile=[Profile.TEST, Profile.DEVELOPMENT])` -- unchanged.
- `Container(profile=Profile.PRODUCTION)` -- unchanged.
- `@service`, `@lifecycle`, `Scope`, `Container` -- all unchanged.
- All framework integrations (FastAPI, Flask, Celery, Click, Django) -- unchanged.

---

## Step-by-step migration

### Step 1: Update your dioxide dependency

```bash
pip install "dioxide>=2.0.0"
# or
uv add "dioxide>=2.0.0"
```

### Step 2: Find and fix `.value` usage

This is the most common change. Search your codebase for `.value` on Profile
instances:

```bash
# Find all .value usage on profiles
grep -rn "\.value" --include="*.py" | grep -i profile
```

Replace every `profile.value` with `str(profile)` or just use the profile
directly:

```python
# Before
if profile.value == "production":
    ...

# After (option A -- use the profile directly)
if profile == "production":
    ...

# After (option B -- explicit str conversion)
if str(profile) == "production":
    ...
```

### Step 3: Find and fix `.name` usage

```bash
# Find .name usage on profiles
grep -rn "\.name" --include="*.py" | grep -i profile
```

Replace with direct string usage or `repr()`:

```python
# Before
logging.info(f"Profile: {profile.name}")

# After
logging.info(f"Profile: {profile}")
```

### Step 4: Find and fix iteration over `Profile`

```bash
# Find iteration patterns
grep -rn "for.*in Profile" --include="*.py"
grep -rn "list(Profile)" --include="*.py"
```

Replace with an explicit list:

```python
# Before
for p in Profile:
    print(p)

# After
for p in [Profile.PRODUCTION, Profile.TEST, Profile.DEVELOPMENT,
          Profile.STAGING, Profile.CI]:
    print(p)
```

### Step 5: Find and fix bracket access

```bash
# Find bracket access patterns
grep -rn "Profile\[" --include="*.py"
```

Replace with attribute access or constructor:

```python
# Before
profile = Profile['PRODUCTION']

# After
profile = Profile.PRODUCTION
```

### Step 6: Run your test suite

```bash
pytest tests/
```

If tests pass, you are done. If any tests fail with `AttributeError: 'Profile'
object has no attribute 'value'` or similar, apply the patterns from steps 2-5
to the failing code.

---

## Automated find-replace patterns

For larger codebases, use these regex find-replace patterns in your editor or
with `sed`:

### Pattern 1: `.value` removal (most common)

```bash
# Find:    any_profile_variable.value
# Replace: str(any_profile_variable)

# sed command (preview first with -n ... p)
sed -n 's/\(profile[a-zA-Z_]*\)\.value/str(\1)/gp' yourfile.py

# Apply:
sed -i '' 's/\(profile[a-zA-Z_]*\)\.value/str(\1)/g' yourfile.py
```

### Pattern 2: Comparison with `.value`

```bash
# Find:    profile.value == "something"
# Replace: profile == "something"

# sed command:
sed -i '' 's/\.value == /== /g' yourfile.py
sed -i '' 's/\.value != /!= /g' yourfile.py
```

### Pattern 3: `.name` removal

```bash
# Find:    profile.name
# Replace: str(profile)

sed -i '' 's/\(profile[a-zA-Z_]*\)\.name/str(\1)/g' yourfile.py
```

### Pattern 4: Bracket access

```bash
# Find:    Profile['PRODUCTION']
# Replace: Profile.PRODUCTION

sed -i '' "s/Profile\['PRODUCTION'\]/Profile.PRODUCTION/g" yourfile.py
sed -i '' "s/Profile\['TEST'\]/Profile.TEST/g" yourfile.py
sed -i '' "s/Profile\['DEVELOPMENT'\]/Profile.DEVELOPMENT/g" yourfile.py
sed -i '' "s/Profile\['STAGING'\]/Profile.STAGING/g" yourfile.py
sed -i '' "s/Profile\['CI'\]/Profile.CI/g" yourfile.py
sed -i '' "s/Profile\['ALL'\]/Profile.ALL/g" yourfile.py
```

### Codemod option for large-scale refactoring

For projects with hundreds of files, consider using [LibCST](https://libcst.readthedocs.io/)
for AST-based automated refactoring. LibCST can match and transform Python code
structurally rather than relying on text patterns:

```python
import libcst as cst
from libcst import matchers as m

class ProfileValueRemover(cst.CSTTransformer):
    """Remove .value from Profile instances."""

    def leave_Attribute(self, original_node, updated_node):
        if m.matches(updated_node.attr, m.Name("value")):
            return updated_node.value  # Drop the .value access
        return updated_node
```

This approach is more reliable than regex for complex codebases where variable
names do not follow predictable patterns.

---

## Package rename: rivet_di to dioxide

If you are migrating from the original `rivet_di` package (pre-v0.2), the
package was renamed to `dioxide` early in development (October 2025), well
before the v1.0 stable release. This rename predates the v1.x to v2.0 migration
and is unrelated to the Profile breaking change.

If you still have `rivet_di` imports:

```bash
# Find old imports
grep -rn "rivet_di" --include="*.py"
grep -rn "rivet-di" requirements*.txt setup.cfg pyproject.toml

# Replace imports
sed -i '' 's/from rivet_di/from dioxide/g' **/*.py
sed -i '' 's/import rivet_di/import dioxide/g' **/*.py

# Update dependency
pip uninstall rivet-di
pip install dioxide
```

---

## Common gotchas

### Gotcha 1: String comparisons still work

Profile is a `str` subclass, so this was valid in v1.x and is still valid in v2.0:

```python
# This works in BOTH v1.x and v2.0
if profile == "production":
    ...
```

If your v1.x code compared profiles as strings (without `.value`), it already
works on v2.0 with no changes.

### Gotcha 2: Type checking differences

If your code uses strict type checking and you were passing `profile.value`
(a `str`) to functions expecting `str`, you can now pass the `Profile` instance
directly since `Profile` is a `str` subclass:

```python
def connect(host: str, profile_name: str) -> None:
    ...

# v1.x
connect("example.com", profile.value)

# v2.0 -- Profile IS a str, pass it directly
connect("example.com", profile)
```

### Gotcha 3: Serialization

If you serialized profiles to JSON or databases using `.value`:

```python
# Before
data = {"profile": profile.value}
json.dumps(data)

# After -- Profile is a str, json.dumps handles it automatically
data = {"profile": profile}
json.dumps(data)  # Works because Profile is a str subclass
```

### Gotcha 4: Deprecation warnings for raw strings

v2.0 emits `DeprecationWarning` when you use raw strings for built-in profile
names. This is a soft nudge toward the canonical pattern, not a breaking change:

```python
# Emits DeprecationWarning in v2.0 (still works, but use the constant)
@adapter.for_(EmailPort, profile='production')  # Warning!

# Preferred
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)  # No warning

# Custom profiles do NOT trigger warnings
@adapter.for_(MetricsPort, profile='integration')  # No warning (custom)
```

---

## Verifying your migration

After applying the changes, run these checks:

```bash
# 1. Run your test suite
pytest tests/

# 2. Check for remaining .value/.name usage
grep -rn "\.value\b" --include="*.py" | grep -iv "# v1"
grep -rn "\.name\b" --include="*.py" | grep -iv "# v1"

# 3. Check for remaining iteration patterns
grep -rn "for.*in Profile:" --include="*.py"
grep -rn "list(Profile)" --include="*.py"

# 4. Run type checking
mypy your_package/
```

If all four pass cleanly, your migration is complete.

---

## Getting help

If you hit a problem not covered here:

- [Open an issue](https://github.com/mikelane/dioxide/issues) with the label
  `migration` and include the v1.x code that is failing.
- [Start a discussion](https://github.com/mikelane/dioxide/discussions) for
  migration questions or patterns you are unsure about.
- Read the [API reference](https://dioxide.readthedocs.io/en/latest/api/index.html)
  for the current v2.0 API.

We take breaking changes seriously and want every migration to be straightforward.
If this guide missed something, please let us know.
