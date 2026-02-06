"""Scan statistics reporting for container.scan()."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScanStats:
    """Statistics from a container.scan() operation.

    Attributes:
        services_registered: Number of @service components registered.
        adapters_registered: Number of @adapter components registered.
        modules_imported: Number of modules imported during package scanning.
        duration_ms: Wall-clock time of the scan in milliseconds.
    """

    services_registered: int
    adapters_registered: int
    modules_imported: int
    duration_ms: float
