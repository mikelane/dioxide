"""Run with PRODUCTION profile — real Slack + Postgres adapters."""

import adapters_prod  # noqa: F401 — registers production adapters

from dioxide import Container
from dioxide.profile_enum import Profile
from service import OrderProcessor

container = Container(profile=Profile.PRODUCTION)
processor = container.resolve(OrderProcessor)
processor.place_order("alice", "Rust in Action")
