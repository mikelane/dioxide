"""Internal module with a service decorator."""

from dioxide import service


@service
class InternalService:
    """Service in an underscore-prefixed module."""

    pass
