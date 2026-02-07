"""Payment adapter — simulates an expensive SDK import."""

import time

# Simulate loading a heavy payment SDK (e.g., stripe)
time.sleep(0.4)

from dioxide import adapter

from myapp.ports import PaymentPort


@adapter.for_(PaymentPort)
class StripeAdapter:
    def charge(self, amount: float) -> str:
        return f"charged ${amount:.2f}"
