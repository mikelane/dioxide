# Demo Narration: Decorator Usage

## Metadata

- Issue: 389
- Recording date: 2026-02-07

---

## Segments

<!-- SEGMENT: title -->
Two decorators. One simple rule. Let me show you how dioxide keeps business logic and infrastructure apart.

<!-- SEGMENT: show_ports -->
First, the ports. These are just Python protocols. They define what your app needs, a notifier and an audit log, without saying how.

<!-- SEGMENT: show_service -->
Now the service. It uses at-service because business logic never changes between environments. Order Processor depends on the ports, not on Slack or Postgres.

<!-- SEGMENT: show_prod_adapters -->
Here are the production adapters. Each one uses at-adapter-dot-for with a profile. Slack Notifier handles notifications. Postgres Audit Log handles compliance. They are wired to the production profile.

<!-- SEGMENT: show_test_adapters -->
And the test adapters. Same ports, different profile. These are fast in-memory fakes. No network, no database. Just lists that record what happened.

<!-- SEGMENT: run_prod -->
Lets run with the production profile. The container scans adapters, resolves the service, and injects Slack and Postgres automatically.

<!-- SEGMENT: run_test -->
Now the test profile. Same service, same code path. But now it uses the fakes. No infrastructure needed. The assertions run against in-memory data.

<!-- SEGMENT: closing -->
At-service for logic that never changes. At-adapter-dot-for for infrastructure that does. That is the only rule you need.
