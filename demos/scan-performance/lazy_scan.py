"""Lazy scan: defers imports until resolve() is called."""

import time

from dioxide import Container

from myapp.ports import EmailPort

container = Container()

start = time.perf_counter()
container.scan("myapp", lazy=True)
elapsed = time.perf_counter() - start

print(f"Lazy scan:  {elapsed:.3f}s  (no modules imported yet)")

start = time.perf_counter()
email = container.resolve(EmailPort)
elapsed = time.perf_counter() - start

print(f"First resolve: {elapsed:.3f}s  (imported only email adapter)")
email.send("user@example.com", "Hello!")
