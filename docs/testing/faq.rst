Testing FAQ
==========

Common questions and honest answers about dioxide's testing philosophy.

.. _faq-why-not-patch:

Why not just use ``@patch``?
----------------------------

**Short answer:** You can. ``@patch`` is a fine tool for specific situations.
But for dependencies at architectural boundaries, fakes give you tests that
are clearer, more robust, and survive refactoring.

Here are the concrete problems that accumulate with ``@patch`` at scale:

Problem 1: Fragile path strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``@patch`` requires the exact import path of the object being patched. When
you restructure code, tests break even though behavior is unchanged.

.. code-block:: python

   # With @patch — breaks if you move the import
   from unittest.mock import patch

   @patch("myapp.services.user_service.email_client.send")
   def test_sends_welcome_email(mock_send):
       mock_send.return_value = True
       register_user("alice@example.com")
       mock_send.assert_called_once()

   # Refactor: move email_client to a shared module
   # Every test using this path string breaks:
   # @patch("myapp.services.user_service.email_client.send")  # NameError!

.. code-block:: python

   # With dioxide fakes — survives restructuring
   async def test_sends_welcome_email(container):
       service = container.resolve(UserService)
       await service.register_user("Alice", "alice@example.com")

       fake_email = container.resolve(EmailPort)
       assert len(fake_email.sent_emails) == 1
       assert fake_email.sent_emails[0]["to"] == "alice@example.com"

   # Restructure freely — test only cares about the port, not import paths

Problem 2: Testing implementation, not behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``@patch`` encourages asserting *how* code works internally rather than *what*
it achieves. This makes tests fragile and obscures intent.

.. code-block:: python

   # With @patch — tests implementation details
   @patch("myapp.services.user_service.db.create_user")
   @patch("myapp.services.user_service.email_client.send")
   def test_user_registration(mock_send, mock_create):
       mock_create.return_value = {"id": "123", "email": "alice@example.com"}
       mock_send.return_value = True

       result = register_user("Alice", "alice@example.com")

       # These assertions know too much about internals:
       mock_create.assert_called_once_with("Alice", "alice@example.com")
       mock_send.assert_called_once_with(
           to="alice@example.com",
           subject="Welcome!",
           body="Hello Alice, thanks for signing up!",
       )

   # Change the email body wording? Test breaks.
   # Change method call order? Test breaks.
   # Extract a helper method? Test breaks.

.. code-block:: python

   # With dioxide fakes — tests observable outcomes
   async def test_user_registration(container):
       service = container.resolve(UserService)
       result = await service.register_user("Alice", "alice@example.com")

       # Assert what happened, not how:
       assert result["email"] == "alice@example.com"

       fake_email = container.resolve(EmailPort)
       assert fake_email.verify_sent_to("alice@example.com")
       assert fake_email.verify_subject_contains("Welcome")

   # Refactor internals freely — test only checks outcomes

Problem 3: Mock objects accept any method call
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``Mock`` object silently accepts calls to methods that don't exist on the real
interface. Your test passes, but production fails.

.. code-block:: python

   # With @patch — mock lies about interface
   @patch("myapp.services.user_service.email_client")
   def test_email_sent(mock_email):
       mock_email.send_email.return_value = True  # Typo: real method is "send"

       register_user("alice@example.com")

       mock_email.send_email.assert_called_once()  # Test passes!
       # But production crashes: AttributeError: 'EmailClient' has no 'send_email'

.. code-block:: python

   # With dioxide fakes — fake implements the real protocol
   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

   # If the protocol changes (e.g., rename "send" to "deliver"),
   # the fake breaks at scan time, not in production

Problem 4: Patch stacking becomes unreadable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a function has multiple dependencies, you stack ``@patch`` decorators.
The argument order is reversed, and the test setup dwarfs the actual assertion.

.. code-block:: python

   # With @patch — stacking nightmare
   @patch("myapp.services.checkout.payment_gateway.charge")
   @patch("myapp.services.checkout.inventory.reserve")
   @patch("myapp.services.checkout.email_client.send")
   @patch("myapp.services.checkout.audit_log.record")
   def test_checkout(mock_audit, mock_email, mock_reserve, mock_charge):
       # Note: argument order is REVERSED from decorator order
       mock_charge.return_value = {"id": "ch_123", "status": "succeeded"}
       mock_reserve.return_value = True
       mock_email.return_value = True
       mock_audit.return_value = None

       result = checkout(cart_id=42, card="4242424242424242")

       mock_charge.assert_called_once()
       mock_reserve.assert_called_once()
       mock_email.assert_called_once()
       mock_audit.assert_called_once()

.. code-block:: python

   # With dioxide fakes — clean and readable
   async def test_checkout(container):
       service = container.resolve(CheckoutService)
       result = await service.checkout(cart_id=42, card="4242424242424242")

       assert result["status"] == "succeeded"

       fake_payment = container.resolve(PaymentGateway)
       assert len(fake_payment.charges) == 1

       fake_email = container.resolve(EmailPort)
       assert fake_email.verify_sent_to("customer@example.com")

When ``@patch`` IS the right choice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``@patch`` remains useful in specific situations:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Use ``@patch`` when...
     - Use fakes when...
   * - Testing third-party code you don't control
     - You control the interface
   * - Legacy code without dependency injection
     - New code designed with dioxide
   * - Patching is surgical (one isolated spot)
     - Multiple tests need the same behavior
   * - Quick prototype or spike
     - Production code with a long lifespan

**Concrete example where @patch is appropriate:**

.. code-block:: python

   # Testing retry behavior around a third-party SDK you can't wrap
   from unittest.mock import patch

   @patch("boto3.client")
   def test_retries_on_throttle(mock_client):
       mock_client.return_value.put_item.side_effect = [
           ClientError({"Error": {"Code": "ThrottlingException"}}, "PutItem"),
           {"ResponseMetadata": {"HTTPStatusCode": 200}},
       ]
       result = save_to_dynamo(item={"id": "123"})
       assert result is True
       assert mock_client.return_value.put_item.call_count == 2

This is fine because you don't control boto3's interface, and wrapping it in a
port just for one test would be over-engineering.

----

.. _faq-fakes-more-work:

Don't fakes require more work?
------------------------------

**Honest answer:** Yes, upfront. Fakes require you to write a small class that
implements the port's interface. A ``@patch`` call is a single decorator.

But consider the total cost over the life of a project:

**Day 1:**

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - ``@patch`` cost
     - Fake cost
   * - 1 decorator + return value = ~3 lines
     - 1 class + methods = ~15 lines

**Day 100 (10+ tests using the same dependency):**

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - ``@patch`` cost
     - Fake cost
   * - 10 decorators, each with its own mock setup
     - 1 fake class, reused by all 10 tests
   * - Each test repeats ``mock_email.return_value = ...``
     - Each test just resolves from container
   * - Path string duplicated 10 times
     - Zero path strings
   * - Rename internal method: fix 10 tests
     - Rename internal method: fix 0 tests

**Fakes pay for themselves after 2-3 tests that use the same dependency.**

The first test is more work. Every subsequent test is less work. And when you
refactor, fakes protect you from false test failures.

**Where the investment is smallest:**

Start with fakes for the dependencies you test most often: databases, email,
payment gateways, and clocks. These are the boundaries where fakes provide the
most value. Pure utility functions don't need fakes at all.

----

.. _faq-external-apis:

What about external APIs I can't fake?
--------------------------------------

**Short answer:** Wrap them in a port. Then fake the port.

You're right that you can't write a fake for Stripe's actual API. But you
shouldn't be calling Stripe directly from your business logic anyway. Wrap
external APIs in a thin adapter behind a port:

.. code-block:: python

   from typing import Protocol
   from dioxide import adapter, Profile

   # Define what your app needs from a payment system
   class PaymentGateway(Protocol):
       async def charge(self, amount_cents: int, card_token: str) -> str: ...
       async def refund(self, charge_id: str) -> None: ...

   # Production: thin wrapper around Stripe
   @adapter.for_(PaymentGateway, profile=Profile.PRODUCTION)
   class StripeGateway:
       def __init__(self):
           import stripe
           self.stripe = stripe

       async def charge(self, amount_cents: int, card_token: str) -> str:
           result = self.stripe.Charge.create(
               amount=amount_cents,
               currency="usd",
               source=card_token,
           )
           return result["id"]

       async def refund(self, charge_id: str) -> None:
           self.stripe.Refund.create(charge=charge_id)

   # Test: fast fake
   @adapter.for_(PaymentGateway, profile=Profile.TEST)
   class FakePaymentGateway:
       def __init__(self):
           self.charges = []
           self.refunds = []
           self.should_fail = False

       async def charge(self, amount_cents: int, card_token: str) -> str:
           if self.should_fail:
               raise PaymentError("Card declined")
           charge_id = f"ch_{len(self.charges) + 1}"
           self.charges.append({"id": charge_id, "amount": amount_cents})
           return charge_id

       async def refund(self, charge_id: str) -> None:
           self.refunds.append(charge_id)

This pattern gives you:

1. **Fast tests** — no network calls to Stripe
2. **Controllable failures** — ``fake.should_fail = True`` to test error paths
3. **Inspectable state** — ``fake.charges`` to verify what was charged
4. **Local development** — run your app without a Stripe account

**What about testing the Stripe wrapper itself?**

The ``StripeGateway`` adapter is a thin wrapper with minimal logic. Test it
separately with integration tests (real Stripe test mode) or, if the wrapper is
truly trivial, trust the Stripe SDK. The key insight is that your business logic
tests don't need Stripe at all — they test against ``PaymentGateway``, the port.

**What about APIs with complex response formats?**

If the external API has complex responses that your code parses, capture real
responses as fixtures and have your fake return them:

.. code-block:: python

   @adapter.for_(WeatherService, profile=Profile.TEST)
   class FakeWeatherService:
       def __init__(self):
           # Real response structure, captured once from the API
           self.forecast = {
               "temperature": 72,
               "conditions": "sunny",
               "humidity": 45,
           }

       async def get_forecast(self, city: str) -> dict:
           return self.forecast

       def set_forecast(self, **kwargs) -> None:
           self.forecast.update(kwargs)

This keeps your fakes honest about the data shape while remaining fast and
controllable.

----

.. seealso::

   - :doc:`philosophy` — Full comparison of mocks vs fakes
   - :doc:`patterns` — Common fake implementation patterns
   - :doc:`fixtures` — Container fixtures for pytest
