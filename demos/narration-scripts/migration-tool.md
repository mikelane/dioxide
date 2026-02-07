# Demo Narration: Migration Experience

## Metadata

- Issue: 410
- Recording date: 2026-02-07

---

## Segments

<!-- SEGMENT: title -->
Every framework upgrade is a gamble. Will your code break? Let's find out.

<!-- SEGMENT: show_v1 -->
Here's a working app built on rivet dee eye version one. It uses adapter dot register, profile enum dot prod, and the old import paths.

<!-- SEGMENT: upgrade_fails -->
You upgrade to dioxide version two. The imports break immediately. Rivet dee eye no longer exists.

<!-- SEGMENT: show_migration -->
But here's the migration guide. Four find-and-replace patterns. Package name, profile enum, decorator API, and container init. That's it.

<!-- SEGMENT: show_v2 -->
After the migration, the code looks almost identical. Adapter dot for underscore replaces adapter dot register. Profile dot production replaces profile enum dot prod.

<!-- SEGMENT: tests_pass -->
We run the tests. They pass. Same logic, same behavior, cleaner API.

<!-- SEGMENT: closing -->
We break APIs when we have to. But we never break your trust. Every breaking change comes with a migration path.
