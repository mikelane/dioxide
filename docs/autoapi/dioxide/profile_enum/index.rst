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


   Profile specification for adapters.

   Profiles determine which adapter implementations are active
   for a given environment. The Profile enum provides standard
   environment profiles used throughout dioxide for adapter selection.

   .. attribute:: PRODUCTION

      Production environment profile

   .. attribute:: TEST

      Test environment profile

   .. attribute:: DEVELOPMENT

      Development environment profile

   .. attribute:: STAGING

      Staging environment profile

   .. attribute:: CI

      Continuous integration environment profile

   .. attribute:: ALL

      Universal profile - available in all environments

   .. admonition:: Examples

      >>> Profile.PRODUCTION
      <Profile.PRODUCTION: 'production'>
      >>> Profile.PRODUCTION.value
      'production'
      >>> str(Profile.TEST)
      'test'
      >>> Profile('production') == Profile.PRODUCTION
      True


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
