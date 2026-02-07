"""Run with PRODUCTION profile — real Slack + Postgres adapters."""

from dioxide import Container
from dioxide.profile_enum import Profile

container = Container()
container.scan("service")
container.scan("adapters_prod", profile=Profile.PRODUCTION)

from service import OrderProcessor

processor = container.resolve(OrderProcessor)
processor.place_order("alice", "Rust in Action")
