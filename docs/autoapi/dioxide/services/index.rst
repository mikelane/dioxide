dioxide.services
================

.. py:module:: dioxide.services

.. autoapi-nested-parse::

   Service decorator for core domain logic.

   The @service decorator marks classes as core domain logic that:
   - Is a singleton (one shared instance across the application)
   - Available in ALL profiles (doesn't vary by environment)
   - Supports constructor-based dependency injection via type hints

   Services represent the core business logic layer in hexagonal architecture,
   sitting between ports (interfaces) and adapters (implementations).



Attributes
----------

.. autoapisummary::

   dioxide.services.T


Functions
---------

.. autoapisummary::

   dioxide.services.service


Module Contents
---------------

.. py:data:: T

.. py:function:: service(cls)

   Mark a class as a core domain service.

   Services are singleton components that represent core business logic.
   They are available in all profiles (production, test, development) and
   support automatic dependency injection.

   This is a specialized form of @component that:
   - Always uses SINGLETON scope (one shared instance)
   - Does not require profile specification (available everywhere)
   - Represents core domain logic in hexagonal architecture

   Usage:
       Basic service:
           >>> from dioxide import service
           >>>
           >>> @service
           ... class UserService:
           ...     def create_user(self, name: str) -> dict:
           ...         return {'name': name, 'id': 1}

       Service with dependencies:
           >>> @service
           ... class EmailService:
           ...     pass
           >>>
           >>> @service
           ... class NotificationService:
           ...     def __init__(self, email: EmailService):
           ...         self.email = email

       Auto-discovery and resolution:
           >>> from dioxide import container
           >>>
           >>> container.scan()
           >>> notifications = container.resolve(NotificationService)
           >>> assert isinstance(notifications.email, EmailService)

   :param cls: The class being decorated.

   :returns: The decorated class with dioxide metadata attached. The class can be
             used normally and will be discovered by Container.scan().

   .. note::

      - Services are always SINGLETON scope
      - Services are available in all profiles
      - Dependencies are resolved from constructor (__init__) type hints
      - For profile-specific implementations, use @component with @profile
