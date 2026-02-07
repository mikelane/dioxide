dioxide.scan_plan
=================

.. py:module:: dioxide.scan_plan

.. autoapi-nested-parse::

   Scan plan module for previewing what container.scan() would discover.



Classes
-------

.. autoapisummary::

   dioxide.scan_plan.ServiceInfo
   dioxide.scan_plan.AdapterInfo
   dioxide.scan_plan.ScanPlan


Functions
---------

.. autoapisummary::

   dioxide.scan_plan.build_scan_plan


Module Contents
---------------

.. py:class:: ServiceInfo

   Information about a discovered @service-decorated class.


   .. py:attribute:: class_name
      :type:  str


   .. py:attribute:: module
      :type:  str


.. py:class:: AdapterInfo

   Information about a discovered @adapter.for_()-decorated class.


   .. py:attribute:: class_name
      :type:  str


   .. py:attribute:: module
      :type:  str


.. py:class:: ScanPlan

   Preview of what container.scan() would discover and import.

   Created by ``container.scan_plan()`` to show which modules would be
   imported and which decorated classes would be found, without actually
   importing any modules or registering any components.

   .. attribute:: modules

      List of fully-qualified module paths that would be imported.

   .. attribute:: services

      List of ``ServiceInfo`` objects for discovered @service classes.

   .. attribute:: adapters

      List of ``AdapterInfo`` objects for discovered @adapter classes.


   .. py:attribute:: modules
      :type:  list[str]
      :value: []



   .. py:attribute:: services
      :type:  list[ServiceInfo]
      :value: []



   .. py:attribute:: adapters
      :type:  list[AdapterInfo]
      :value: []



   .. py:method:: __repr__()


.. py:function:: build_scan_plan(package_name)

   Build a scan plan by walking a package and parsing AST.

   This discovers modules and their dioxide decorators without importing
   any modules. Uses ``importlib.util.find_spec`` for package location
   and ``ast.parse`` for decorator discovery.
