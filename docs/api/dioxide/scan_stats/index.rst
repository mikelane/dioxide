dioxide.scan_stats
==================

.. py:module:: dioxide.scan_stats

.. autoapi-nested-parse::

   Scan statistics reporting for container.scan().



Classes
-------

.. autoapisummary::

   dioxide.scan_stats.ScanStats


Module Contents
---------------

.. py:class:: ScanStats

   Statistics from a container.scan() operation.

   .. attribute:: services_registered

      Number of @service components registered.

   .. attribute:: adapters_registered

      Number of @adapter components registered.

   .. attribute:: modules_imported

      Number of modules imported during package scanning.

   .. attribute:: duration_ms

      Wall-clock time of the scan in milliseconds.


   .. py:attribute:: services_registered
      :type:  int


   .. py:attribute:: adapters_registered
      :type:  int


   .. py:attribute:: modules_imported
      :type:  int


   .. py:attribute:: duration_ms
      :type:  float
