SideEffectWarning
=================

.. contents::
   :local:
   :depth: 2

Overview
--------

``SideEffectWarning`` is emitted when ``container.scan(strict=True)`` detects
potential module-level side effects during AST analysis. This warning helps you
identify modules that perform I/O, network calls, or other side effects at
import time.

.. note::

   ``SideEffectWarning`` is a **warning** (``UserWarning`` subclass), not an
   exception. It does not stop execution by default. Use the ``warnings``
   module to escalate it to an error if desired.

Example Warning
---------------

.. code-block:: text

   SideEffectWarning: Module 'myapp.adapters.email' contains potential side effects:
     - Line 12: Function call 'requests.get(...)' at module level

What Causes This
----------------

Strict mode uses AST analysis to detect function calls at module level that may
cause side effects. Common triggers include:

1. **Network calls at import time**: ``requests.get()``, ``urllib.urlopen()``
2. **Database connections at import time**: ``psycopg2.connect()``, ``create_engine()``
3. **File I/O at import time**: ``open()``, ``Path().read_text()``
4. **Environment setup at import time**: ``logging.basicConfig()``, ``os.makedirs()``

Example
-------

.. code-block:: python

   # myapp/adapters/email.py

   import requests

   # This triggers SideEffectWarning: module-level function call
   API_KEY = requests.get("https://vault.example.com/key").text

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       def __init__(self):
           self.api_key = API_KEY

When scanned with strict mode:

.. code-block:: python

   container = Container(profile=Profile.PRODUCTION)
   container.scan("myapp", strict=True)  # SideEffectWarning!

Solutions
---------

1. Defer Side Effects to Initialize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Move side effects into ``@lifecycle`` initialization:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   @lifecycle
   class SendGridAdapter:
       async def initialize(self) -> None:
           import requests
           self.api_key = requests.get("https://vault.example.com/key").text

       async def dispose(self) -> None:
           pass

2. Use Lazy Initialization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Defer the work until first use:

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       def __init__(self, config: ConfigPort):
           self.api_key = config.get("SENDGRID_API_KEY")

3. Use Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read configuration from environment variables instead of remote calls:

.. code-block:: python

   import os

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       def __init__(self):
           self.api_key = os.environ["SENDGRID_API_KEY"]

Controlling Warnings
--------------------

Filter warnings using the standard ``warnings`` module:

.. code-block:: python

   import warnings
   from dioxide.exceptions import SideEffectWarning

   # Suppress all side-effect warnings
   warnings.filterwarnings("ignore", category=SideEffectWarning)

   # Escalate to errors (fail-fast)
   warnings.filterwarnings("error", category=SideEffectWarning)

   # Suppress for a specific module only
   warnings.filterwarnings(
       "ignore",
       category=SideEffectWarning,
       message=".*myapp\\.legacy.*",
   )

When to Use Strict Mode
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Use ``strict=True``
     - Skip ``strict=True``
   * - New projects with clean imports
     - Legacy codebases with unavoidable side effects
   * - CI pipelines to enforce import hygiene
     - Quick prototyping and scripts
   * - Libraries that others will import
     - Applications with controlled startup

Best Practices
--------------

1. **Keep module-level code pure**: Only imports, class/function definitions, and constants
2. **Defer I/O to lifecycle hooks**: Use ``@lifecycle`` for initialization that requires I/O
3. **Use environment variables for config**: Read from ``os.environ`` instead of remote calls
4. **Enable strict mode in CI**: Catch import side effects before they reach production
5. **Use lazy scanning**: ``container.scan("myapp", lazy=True)`` defers imports entirely

See Also
--------

- :doc:`/guides/scan-performance` - Scan modes and performance
- :doc:`/user_guide/package_scanning` - Package scanning overview
- :doc:`/guides/lifecycle-async-patterns` - Lifecycle management patterns
