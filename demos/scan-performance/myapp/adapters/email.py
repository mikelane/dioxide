"""Email adapter — simulates an expensive SDK import."""

import time

# Simulate loading a heavy email SDK (e.g., boto3, sendgrid)
time.sleep(0.4)

from dioxide import adapter

from myapp.ports import EmailPort


@adapter.for_(EmailPort)
class SendGridAdapter:
    def send(self, to: str, body: str) -> None:
        print(f"  Sent email to {to}")
