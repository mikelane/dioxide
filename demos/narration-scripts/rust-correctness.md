# Demo Narration: Rust Backend Correctness Guarantees

## Metadata

- Issue: 393
- Recording date: 2026-02-07

---

## Segments

<!-- SEGMENT: title -->
Most dependency injection frameworks let wiring errors slip through to runtime. dioxide catches them before your app starts.

<!-- SEGMENT: show_missing -->
Here is an Order Service that depends on a Notification Port. But we forgot to register an adapter. Watch what happens when we resolve it.

<!-- SEGMENT: run_missing -->
dioxide stops immediately. The error tells you exactly which port is missing, which profile you scanned, and even shows you the fix. No guessing, no stack trace spelunking.

<!-- SEGMENT: show_circular -->
Now a trickier bug. Auth Service depends on User Service, and User Service depends right back on Auth Service. A circular dependency.

<!-- SEGMENT: run_circular -->
The Rust backend walks the dependency graph and catches the cycle at resolution time. This would be a stack overflow at 2 AM in other frameworks. dioxide catches it at startup.

<!-- SEGMENT: show_correct -->
When the wiring is correct, resolution is instant. The adapter is injected, the service works, and you ship with confidence.

<!-- SEGMENT: closing -->
Fail fast. Fail at startup. That is what the Rust backend guarantees.
