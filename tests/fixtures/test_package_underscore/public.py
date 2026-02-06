"""Public module with a service decorator."""

from dioxide import service


@service
class PublicService:
    """Service in a public module."""

    pass
