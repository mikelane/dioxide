# Demo Narration: Scan Performance

## Metadata

- Issue: 385
- Recording date: 2026-02-07

---

## Segments

<!-- SEGMENT: title -->
How fast does your app start? Let's see what happens when dioxide scans a package with expensive imports.

<!-- SEGMENT: show_adapters -->
Here are three adapters. Each one simulates a heavy SDK import, like Stripe or SendGrid, with a point-four second sleep at module level.

<!-- SEGMENT: eager_scan -->
With eager scanning, dioxide imports every module upfront. Three adapters, each sleeping point-four seconds. Over a second just to start up.

<!-- SEGMENT: run_eager -->
Watch. One-point-two seconds. All three adapters loaded, whether you need them or not.

<!-- SEGMENT: lazy_intro -->
Now the same package, but with lazy equals true. Dioxide reads the source code with AST parsing. No imports. No sleeps.

<!-- SEGMENT: run_lazy -->
One millisecond. The container knows what's available, but nothing has been imported yet.

<!-- SEGMENT: first_resolve -->
When you resolve a port, only that adapter gets imported. One module, point-four seconds, instead of all three.

<!-- SEGMENT: closing -->
Lazy scanning. Load what you need, when you need it.
