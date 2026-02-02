dioxide.profile_enum
====================

.. py:module:: dioxide.profile_enum

.. autoapi-nested-parse::

   Profile class for hexagonal architecture adapter selection.

   This module defines the Profile class that specifies which adapter
   implementations should be active for a given environment.

   Profile is an extensible, type-safe string subclass that allows both
   built-in profiles and custom user-defined profiles.



Classes
-------

.. autoapisummary::

   dioxide.profile_enum.Profile


Module Contents
---------------

.. py:class:: Profile

   Bases: :py:obj:`str`


   Extensible, type-safe profile identifier for adapter selection.

   Profile is a string subclass that provides type safety while remaining
   fully extensible. Built-in profiles are available as class attributes,
   and users can create custom profiles for their specific needs.

   **Built-in Profiles**:

   - ``Profile.PRODUCTION`` - Production environment
   - ``Profile.TEST`` - Test environment
   - ``Profile.DEVELOPMENT`` - Development environment
   - ``Profile.STAGING`` - Staging environment
   - ``Profile.CI`` - Continuous integration environment
   - ``Profile.ALL`` - Universal profile (matches all environments)

   **Usage**:

   Use built-in profiles for common environments::

       @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
       @adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
       @adapter.for_(LogPort, profile=Profile.ALL)

   Create custom profiles for specific needs::

       # Define custom profiles (type-safe)
       INTEGRATION = Profile('integration')
       PREVIEW = Profile('preview')
       LOAD_TEST = Profile('load-test')

       @adapter.for_(Port, profile=INTEGRATION)
       @adapter.for_(Port, profile=[PREVIEW, Profile.STAGING])

   **Type Safety**:

   All profiles are instances of ``Profile``, providing static type checking::

       def configure(profile: Profile) -> None: ...


       configure(Profile.PRODUCTION)  # OK
       configure(Profile('custom'))  # OK
       configure('raw-string')  # Type error (if strict)

   **Backward Compatibility**:

   Profile is a ``str`` subclass, so it works anywhere strings are expected.
   Raw strings are still accepted at runtime for backward compatibility,
   but using ``Profile(...)`` is recommended for type safety.

   .. admonition:: Examples

      >>> Profile.PRODUCTION
      'production'
      >>> Profile.PRODUCTION == 'production'
      True
      >>> isinstance(Profile.PRODUCTION, str)
      True
      >>> Profile('custom') == 'custom'
      True
      >>> type(Profile('custom'))
      <class 'dioxide.profile_enum.Profile'>


   .. py:attribute:: PRODUCTION
      :type:  ClassVar[Profile]


   .. py:attribute:: TEST
      :type:  ClassVar[Profile]


   .. py:attribute:: DEVELOPMENT
      :type:  ClassVar[Profile]


   .. py:attribute:: STAGING
      :type:  ClassVar[Profile]


   .. py:attribute:: CI
      :type:  ClassVar[Profile]


   .. py:attribute:: ALL
      :type:  ClassVar[Profile]


   .. py:method:: __repr__()

      Return a detailed string representation.

      .. admonition:: Examples

         >>> repr(Profile.PRODUCTION)
         "Profile('production')"
         >>> repr(Profile('custom'))
         "Profile('custom')"
