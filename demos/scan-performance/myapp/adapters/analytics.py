"""Analytics adapter — simulates an expensive SDK import."""

import time

# Simulate loading a heavy analytics SDK (e.g., segment)
time.sleep(0.4)

from dioxide import adapter

from myapp.ports import AnalyticsPort


@adapter.for_(AnalyticsPort)
class SegmentAdapter:
    def track(self, event: str) -> None:
        print(f"  Tracked: {event}")
