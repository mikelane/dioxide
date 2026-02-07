dioxide.deprecation
===================

.. py:module:: dioxide.deprecation

.. autoapi-nested-parse::

   Deprecation warning infrastructure for dioxide.

   Provides the ``deprecated()`` decorator for marking functions and methods
   as deprecated with structured warning messages that include version
   information and migration guidance.



Functions
---------

.. autoapisummary::

   dioxide.deprecation.deprecated


Module Contents
---------------

.. py:function:: deprecated(*, since, removed_in, alternative = None)

   Mark a function or method as deprecated.

   :param since: The version when this was deprecated (e.g., '2.0.0').
   :param removed_in: The version when this will be removed (e.g., '3.0.0').
   :param alternative: What to use instead (e.g., 'str(profile)').

   :returns: A decorator that wraps the function to emit a DioxideDeprecationWarning
             when called.
