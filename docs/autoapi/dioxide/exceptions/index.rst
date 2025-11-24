dioxide.exceptions
==================

.. py:module:: dioxide.exceptions

.. autoapi-nested-parse::

   Custom exception classes for dioxide dependency injection errors.

   This module defines descriptive exception classes that provide helpful, actionable
   error messages when dependency resolution fails. These exceptions replace generic
   KeyError exceptions with detailed information about what went wrong and how to fix it.



Exceptions
----------

.. autoapisummary::

   dioxide.exceptions.AdapterNotFoundError
   dioxide.exceptions.ServiceNotFoundError
   dioxide.exceptions.CircularDependencyError


Module Contents
---------------

.. py:exception:: AdapterNotFoundError

   Bases: :py:obj:`Exception`


   Initialize self.  See help(type(self)) for accurate signature.


.. py:exception:: ServiceNotFoundError

   Bases: :py:obj:`Exception`


   Initialize self.  See help(type(self)) for accurate signature.


.. py:exception:: CircularDependencyError

   Bases: :py:obj:`Exception`


   Initialize self.  See help(type(self)) for accurate signature.
