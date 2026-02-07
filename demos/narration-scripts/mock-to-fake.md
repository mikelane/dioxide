# Demo Narration: Mock-to-Fake Migration

## Metadata

- Issue: 404
- Recording date: 2026-02-07

---

## Segments

<!-- SEGMENT: title -->
Watch what happens when you refactor code that's tested with mocks.

<!-- SEGMENT: show_service -->
Here's a typical email service. It imports smtplib directly and sends messages through SMTP.

<!-- SEGMENT: show_mock_test -->
The test uses at-patch to mock smtplib, asserting on starttls, login, and send message. Everything passes.

<!-- SEGMENT: explain_refactor -->
Now the business says switch from SMTP to a REST API. Same behavior, different transport. We refactor the service to use an HTTP endpoint instead.

<!-- SEGMENT: mock_breaks -->
We run the same mock test and it explodes. The mock was patching app dot smtplib, which no longer exists. The test was coupled to the implementation, not the behavior.

<!-- SEGMENT: show_dioxide -->
Now here's the dioxide way. The service depends on an email port protocol. It doesn't know or care whether emails go through SMTP, an API, or a carrier pigeon.

<!-- SEGMENT: show_fake_test -->
The test uses a simple fake. Seven lines of code. It records what was sent and lets us assert on the result.

<!-- SEGMENT: fake_survives -->
Same refactoring. Same test. It passes. Because the fake implements the port, not the implementation.

<!-- SEGMENT: closing -->
Mocks couple to how. Fakes couple to what. That's why fakes survive refactoring.
