"""Module that will fail to import."""

# This will cause an ImportError when imported

from dioxide import component


@component
class BrokenService:
    """This service won't be registered due to import error."""

    pass
