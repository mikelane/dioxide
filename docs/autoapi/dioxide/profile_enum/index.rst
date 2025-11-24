dioxide.profile_enum
====================

.. py:module:: dioxide.profile_enum

.. autoapi-nested-parse::

   Profile enum for hexagonal architecture adapter selection.

   This module defines the Profile enum that specifies which adapter
   implementations should be active for a given environment.



Classes
-------

.. autoapisummary::

   dioxide.profile_enum.Profile


Module Contents
---------------

.. py:class:: Profile

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Initialize self.  See help(type(self)) for accurate signature.


   .. py:attribute:: PRODUCTION
      :value: 'production'



   .. py:attribute:: TEST
      :value: 'test'



   .. py:attribute:: DEVELOPMENT
      :value: 'development'



   .. py:attribute:: STAGING
      :value: 'staging'



   .. py:attribute:: CI
      :value: 'ci'



   .. py:attribute:: ALL
      :value: '*'
