"""Eager scan: imports every module at startup."""

import time

from dioxide import Container

container = Container()

start = time.perf_counter()
container.scan("myapp")
elapsed = time.perf_counter() - start

print(f"Eager scan: {elapsed:.3f}s  (loaded all 3 adapters)")
