Fakes in Production Code: The Deployment Story
=================================================

"Fakes live in production code" sounds alarming. This page explains exactly what
that means, why it's safe, and why it's actually a better design than the alternative.

.. contents:: On This Page
   :local:
   :depth: 2

----

"It Feels Wrong Because..."
----------------------------

If you're uncomfortable with fakes in your source tree, you're not alone. Here are
the concerns developers typically raise:

1. **"Test code shouldn't ship to production"** -- You're right, and it doesn't.
   The code is *present* in the package, but it never *executes* in production.
2. **"Won't fakes bloat my deployment?"** -- A handful of simple classes with dict
   storage adds kilobytes, not megabytes. Your real adapters are orders of magnitude
   larger.
3. **"What if someone accidentally uses a fake in production?"** -- The profile system
   makes this structurally impossible, not just procedurally discouraged.

Let's address each one.

----

How Profile-Based Registration Works
--------------------------------------

The key insight: ``@adapter.for_(..., profile=Profile.TEST)`` is a **registration
declaration**, not an activation. The adapter is only instantiated when the container
runs with a matching profile.

.. code-block:: python

   from dioxide import adapter, Profile, Container
   from typing import Protocol

   class UserRepository(Protocol):
       async def find_by_id(self, user_id: int) -> dict | None: ...

   # Registered for PRODUCTION profile
   @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   class PostgresUserRepository:
       async def find_by_id(self, user_id: int) -> dict | None:
           # Real database query
           ...

   # Registered for TEST profile
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class FakeUserRepository:
       def __init__(self):
           self.users: dict[int, dict] = {}

       async def find_by_id(self, user_id: int) -> dict | None:
           return self.users.get(user_id)

When your production application starts:

.. code-block:: python

   # In production startup
   container = Container(profile=Profile.PRODUCTION)

   # The container ONLY registers adapters matching Profile.PRODUCTION
   repo = container.resolve(UserRepository)
   # Returns PostgresUserRepository -- NEVER FakeUserRepository

Here's what happens at each stage:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Stage
     - PostgresUserRepository
     - FakeUserRepository
   * - Import time
     - Class defined, decorator registers it for PRODUCTION
     - Class defined, decorator registers it for TEST
   * - ``Container(profile=PRODUCTION)``
     - Eligible for resolution
     - **Not eligible** (profile mismatch)
   * - ``container.resolve(UserRepository)``
     - Instantiated and returned
     - **Never instantiated**

The fake class exists as Python bytecode in memory, just like any other unused import.
It occupies zero runtime resources beyond its class definition.

----

Code Present vs. Code Executed
-------------------------------

This distinction is fundamental. Python imports modules and defines classes at import
time, but that doesn't mean those classes are used.

Consider standard library code you import every day:

.. code-block:: python

   import os

   # os contains hundreds of functions you never call.
   # os.fork() exists on macOS but you don't worry about it "shipping."
   # You only call the functions you need.

Fakes work the same way. The class definition exists. The constructor never runs.
No instance is created. No state is allocated. No methods are called.

**What "fakes in production code" actually means:**

.. code-block:: text

   What it sounds like: Fake implementations are executing in production
   What it actually is: Fake class definitions exist in the source tree

   Your production server:
     - Imports the module ........... yes (class definition loaded)
     - Registers the fake ........... yes (stored in adapter registry)
     - Profile matches PRODUCTION ... no  (TEST != PRODUCTION)
     - Instantiates the fake ........ NO
     - Calls any fake method ........ NO
     - Allocates any fake state ..... NO

----

Size Impact: The Numbers
-------------------------

Fakes are simple by design. Here's a realistic size comparison:

.. code-block:: text

   Typical project layout:
   ================================================================
   Production adapters (Postgres, SendGrid, Redis, S3)    ~2,000 lines
   Domain services and business logic                     ~5,000 lines
   Framework integration (FastAPI routes, middleware)      ~1,500 lines
   Configuration and startup                              ~500 lines
   ----------------------------------------------------------------
   Total production code                                  ~9,000 lines

   Fake adapters (dict storage, list capture, flag toggles)  ~200 lines
   ----------------------------------------------------------------
   Fakes as percentage of codebase                        ~2%

Fakes are intentionally simpler than real adapters. A ``FakeUserRepository`` is a dict
wrapper (10-20 lines). A ``PostgresUserRepository`` has connection pooling, query
building, error handling, and migrations (200+ lines).

In terms of package size, a typical dioxide project's ``.whl`` file:

.. code-block:: text

   Without fakes:  ~45 KB
   With fakes:     ~47 KB
   Difference:     ~2 KB  (the size of a few Python classes)

For comparison, a single production dependency like ``sqlalchemy`` adds ~3 MB.

----

Safety Guarantees
------------------

The profile system provides **structural safety**, not just convention. You don't need
to "remember" not to use fakes in production. The system prevents it.

Guarantee 1: Profile mismatch prevents resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   container = Container(profile=Profile.PRODUCTION)

   # This resolves to PostgresUserRepository, period.
   repo = container.resolve(UserRepository)
   assert isinstance(repo, PostgresUserRepository)  # Always true

   # There is no API to "bypass" the profile and get the fake.
   # The container doesn't even know how to instantiate FakeUserRepository
   # when running in PRODUCTION profile.

Guarantee 2: Missing adapter fails fast
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you accidentally forget to register a production adapter, the container fails at
startup with a clear error, not at runtime with a subtle bug:

.. code-block:: python

   # If PostgresUserRepository is missing:
   container = Container(profile=Profile.PRODUCTION)
   container.resolve(UserRepository)
   # Raises: AdapterNotFoundError:
   #   No adapter registered for UserRepository with profile 'production'.
   #   Available profiles: ['test']

This is a startup error, caught during deployment, not a production incident.

Guarantee 3: No accidental cross-profile leakage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each container instance is locked to one profile. There is no way for a
``Profile.TEST`` adapter to "leak" into a ``Profile.PRODUCTION`` container:

.. code-block:: python

   prod_container = Container(profile=Profile.PRODUCTION)
   test_container = Container(profile=Profile.TEST)

   # Each resolves its own adapter
   prod_repo = prod_container.resolve(UserRepository)   # PostgresUserRepository
   test_repo = test_container.resolve(UserRepository)    # FakeUserRepository

   # No cross-contamination possible

----

Where Fakes Go in Your Project
-------------------------------

Fakes live alongside their real counterparts, organized by the port they implement:

.. code-block:: text

   myapp/
     domain/
       ports.py                      # Protocol definitions
       services.py                   # Business logic (@service)

     adapters/
       postgres_users.py             # @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
       sendgrid_email.py             # @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
       system_clock.py               # @adapter.for_(Clock, profile=Profile.PRODUCTION)

       fake_users.py                 # @adapter.for_(UserRepository, profile=Profile.TEST)
       fake_email.py                 # @adapter.for_(EmailPort, profile=Profile.TEST)
       fake_clock.py                 # @adapter.for_(Clock, profile=Profile.TEST)

   tests/
     conftest.py                     # Fixtures that resolve fakes from container
     test_user_service.py            # Tests using fakes

**Why this layout works well:**

- When ``UserRepository`` protocol changes, both ``postgres_users.py`` and
  ``fake_users.py`` need updating. They're right next to each other, so drift is
  immediately visible.
- Any developer can see at a glance which ports have which implementations.
- IDE "find implementations" shows both real and fake adapters together.

----

Build and Deploy Pipeline
--------------------------

In a standard Python deployment, fakes are included in the wheel but remain dormant.

.. code-block:: text

   Development:
     pip install -e .                 # Fakes available for local dev
     Container(profile=Profile.DEVELOPMENT)

   Testing (CI):
     pip install .                    # Fakes available for test suite
     Container(profile=Profile.TEST)

   Production:
     pip install .                    # Fakes present but dormant
     Container(profile=Profile.PRODUCTION)  # Only PRODUCTION adapters activate

The wheel file contains all ``.py`` files from your package. The profile system
determines which classes are actually used at runtime.

**Runtime cost of dormant fakes**: Zero. Python loads the class definition (a few
hundred bytes of bytecode), but no instance is ever created, no methods are called,
and no state is allocated.

----

If You Really Want to Exclude Fakes
-------------------------------------

For teams with strict deployment policies (e.g., security compliance that requires
minimizing shipped code), you can exclude fake modules from production builds.

Option 1: Separate package
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   myapp/                            # Production package
     adapters/
       postgres_users.py
       sendgrid_email.py

   myapp-testing/                    # Testing extras package
     adapters/
       fake_users.py
       fake_email.py
       fake_clock.py

.. code-block:: toml

   # pyproject.toml
   [project.optional-dependencies]
   testing = ["myapp-testing"]

.. code-block:: bash

   # Production: install without fakes
   pip install myapp

   # Testing: install with fakes
   pip install myapp[testing]

Option 2: Exclude patterns in build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   # pyproject.toml - exclude fake modules from wheel
   [tool.setuptools.packages.find]
   exclude = ["myapp.adapters.fake_*"]

Option 3: Conditional imports with environment variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # myapp/adapters/__init__.py
   import os

   if os.environ.get("MYAPP_PROFILE") != "production":
       from myapp.adapters import fake_users    # noqa: F401
       from myapp.adapters import fake_email    # noqa: F401
       from myapp.adapters import fake_clock    # noqa: F401

.. warning::

   **We don't recommend any of these options for most teams.** They add build
   complexity, create divergence between what you test and what you deploy, and
   solve a problem that doesn't exist in practice (dormant classes have zero
   runtime cost).

   The simplest, safest approach is to ship fakes and let the profile system
   handle activation. This is what dioxide is designed for.

----

Why It's Actually Good
-----------------------

Once you get past the initial discomfort, fakes in production code provide real benefits:

**1. Fakes stay in sync with ports**

When both the real adapter and the fake live in the same package, changes to the
port's protocol cause both to need updating. If you move fakes to a separate package,
they can silently drift out of sync.

**2. Developers can run the app without infrastructure**

.. code-block:: bash

   # No PostgreSQL, no Redis, no SendGrid needed
   MYAPP_PROFILE=development python -m myapp

   # In-memory fakes let new developers start immediately
   # No Docker, no docker-compose, no .env files

**3. Fakes document the port contract**

A fake is a readable specification of what the port expects. New developers can
read ``FakeUserRepository`` to understand the ``UserRepository`` protocol without
wading through SQL queries and connection management.

**4. One source of truth for all environments**

.. code-block:: text

   Same package, same code:
     production  → Container(profile=Profile.PRODUCTION)  → real adapters
     staging     → Container(profile=Profile.STAGING)      → real adapters
     development → Container(profile=Profile.DEVELOPMENT)  → fakes
     testing     → Container(profile=Profile.TEST)          → fakes

No separate "test utilities" package that might be on a different version.
No "works in test but breaks in production" surprises.

**5. Zero overhead**

A class definition that's never instantiated costs nothing at runtime. Python loads
thousands of class definitions you never use on every startup (look at the standard
library). A few fake adapters are invisible in the noise.

----

FAQ
----

**Q: What if a developer manually instantiates a fake in production code?**

They would have to deliberately bypass the container and import the fake class
directly. This is the same as any other code quality issue -- you wouldn't write
``repo = FakeUserRepository()`` in a production handler any more than you'd write
``repo = None``. Code review catches this, and the container's profile system makes
it unnecessary.

**Q: Do fakes appear in API documentation (e.g., autodoc)?**

Only if you configure your documentation tool to include them. Standard Sphinx autodoc
respects ``__all__`` exports and module-level configuration. You can exclude fake
modules from API docs while keeping them in the package.

**Q: What about compiled/obfuscated deployments?**

If you're compiling Python to ``.pyc`` only or using tools like PyArmor, fakes are
compiled along with everything else. The profile system still applies at runtime.
If you need to exclude them from compiled artifacts, use the build exclusion patterns
described above.

**Q: Doesn't this violate the Single Responsibility Principle?**

No. The *package* contains both production and test adapters, but each *class* has
a single responsibility. ``PostgresUserRepository`` handles database operations.
``FakeUserRepository`` handles in-memory test storage. They implement the same port
but serve different purposes in different environments.

.. seealso::

   - :doc:`philosophy` - Why fakes over mocks
   - :doc:`patterns` - Common testing patterns with fakes
   - :doc:`/user_guide/hexagonal_architecture` - Understanding ports, adapters, and profiles
