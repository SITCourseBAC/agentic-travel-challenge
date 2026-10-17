"""Official SDK/instructor checks and four unfinished Week 3 student tasks."""

import asyncio
import subprocess
import sys

import httpx
import pytest
from pydantic import ValidationError
from x402 import PaymentRequired, SettleResponse
from x402.http.utils import (
    decode_payment_required_header, decode_payment_response_header,
    encode_payment_signature_header,
)

from travel_challenge.week3 import paid_weather


@pytest.fixture
def purchase():
    from travel_challenge.week3 import authorization

    return authorization.hotel_purchase({
        "within_budget": True,
        "request": {"departure_date": "2027-03-20", "return_date": "2027-03-23", "currency": "SGD"},
        "hotel": {"id": "test-offer", "merchant_id": "test-hotel", "merchant_name": "Test Hotel",
                  "amount_cents": 301529, "currency": "SGD", "rooms": 5},
    })


@pytest.fixture
def mandates(purchase):
    from travel_challenge.week3 import authorization

    token, binding = authorization.signed_checkout(purchase)
    return (
        authorization.CheckoutMandate(checkout_jwt=token, checkout_hash=binding),
        authorization.PaymentMandate(
            transaction_id=binding, payee={"id": purchase["merchant_id"], "name": purchase["merchant_name"]},
            payment_amount={"amount": purchase["amount_cents"], "currency": purchase["currency"]},
            payment_instrument={"id": "course-card", "type": "simulated"},
        ),
    )


@pytest.mark.scaffold
def test_x402_imports_without_travel_or_ap2():
    result = subprocess.run([sys.executable, "-c", (
        "import sys; from travel_challenge.week3 import paid_weather; "
        "assert not any(name.startswith(('a2a', 'mcp', 'ap2', "
        "'travel_challenge.week3.authorization', 'travel_challenge.week1.nuitee_rest', "
        "'travel_challenge.week1.trip_planner')) for name in sys.modules)"
    )], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.scaffold
def test_official_x402_http_signing_and_simulated_receipt():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=paid_weather.app), base_url="http://test") as http:
            response = await http.get("/weather?city=Tokyo")
            assert response.status_code == 402
            required = decode_payment_required_header(response.headers["PAYMENT-REQUIRED"])
            assert isinstance(required, PaymentRequired)
            assert required.accepts[0].amount == "3000"
            payload = await paid_weather.make_payment_client().create_payment_payload(required)
            paid = await http.get(response.request.url, headers={"PAYMENT-SIGNATURE": encode_payment_signature_header(payload)})
            assert paid.status_code == 200
            receipt = decode_payment_response_header(paid.headers["PAYMENT-RESPONSE"])
            assert receipt.success and receipt.transaction.startswith("SIMULATED:")
            assert paid.json()["settlement"] == "SIMULATED_NO_FUNDS_MOVED"

    asyncio.run(run())


@pytest.mark.scaffold
def test_weather_rejects_tampered_or_malformed_signatures():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=paid_weather.app), base_url="http://test") as http:
            response = await http.get("/weather")
            required = decode_payment_required_header(response.headers["PAYMENT-REQUIRED"])
            payload = await paid_weather.make_payment_client().create_payment_payload(required)
            for field, value in [("value", "9999"), ("from", "0x0000000000000000000000000000000000000002"), ("validBefore", "1")]:
                changed = payload.model_copy(deep=True)
                changed.payload["authorization"][field] = value
                rejected = await http.get("/weather", headers={"PAYMENT-SIGNATURE": encode_payment_signature_header(changed)})
                assert rejected.status_code == 403
            payload.payload["signature"] = "0x00"
            rejected = await http.get("/weather", headers={"PAYMENT-SIGNATURE": encode_payment_signature_header(payload)})
            assert rejected.status_code == 403
            assert (await http.get("/weather", headers={"PAYMENT-SIGNATURE": "invalid"})).status_code == 403

    asyncio.run(run())


@pytest.mark.scaffold
def test_official_ap2_models_and_local_merchant_signature(purchase, mandates):
    from travel_challenge.week3 import authorization

    checkout, payment = mandates
    assert authorization.verified_checkout(checkout) == purchase
    assert authorization.PaymentMandate.model_validate_json(payment.model_dump_json()) == payment
    with pytest.raises(ValidationError):
        authorization.PaymentMandate.model_validate({**payment.model_dump(), "payment_amount": {"amount": "invalid", "currency": "SGD"}})
    changed = checkout.model_copy(update={"checkout_hash": "changed"})
    with pytest.raises(ValueError):
        authorization.verified_checkout(changed)
    replacement, unused_binding = authorization.signed_checkout({**purchase, "amount_cents": 1})
    parts = checkout.checkout_jwt.split(".")
    parts[1] = replacement.split(".")[1]
    token = ".".join(parts)
    forged = authorization.CheckoutMandate(checkout_jwt=token, checkout_hash=authorization.checkout_hash(token))
    with pytest.raises(ValueError, match="signature"):
        authorization.verified_checkout(forged)


@pytest.mark.scaffold
def test_explicit_consent_and_detached_approval(monkeypatch, purchase, mandates):
    from travel_challenge.week3 import authorization

    monkeypatch.setattr(authorization, "check_authorization", lambda *args: True)
    with pytest.raises(PermissionError):
        authorization.approve_purchase(purchase, *mandates, consent=False)
    snapshot = authorization.approve_purchase(purchase, *mandates, consent=True)
    purchase["amount_cents"] += 1
    assert snapshot["amount_cents"] == 301529
    monkeypatch.setattr(authorization, "check_authorization", lambda *args: False)
    with pytest.raises(PermissionError):
        authorization.approve_purchase(purchase, *mandates, consent=True)


@pytest.mark.student
def test_student_reads_actual_x402():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=paid_weather.app), base_url="http://test") as http:
            response = await http.get("/weather")
            required = paid_weather.read_requirements(response)
            assert isinstance(required, PaymentRequired)
            assert required.accepts[0].amount == "3000"
            assert required.accepts[0].network == "eip155:84532"
    asyncio.run(run())


@pytest.mark.student
def test_student_pays_with_official_x402_sdk():
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=paid_weather.app), base_url="http://test") as http:
            response = await http.get("/weather?city=Tokyo")
            weather, receipt = await paid_weather.pay_for_weather(http, response)
            assert weather["city"] == "Tokyo"
            assert weather["settlement"] == "SIMULATED_NO_FUNDS_MOVED"
            assert isinstance(receipt, SettleResponse) and receipt.success
    asyncio.run(run())


@pytest.mark.student
def test_student_constructs_official_ap2_models(purchase):
    from travel_challenge.week3 import authorization

    checkout, payment = authorization.make_mandates(purchase)
    assert isinstance(checkout, authorization.CheckoutMandate)
    assert isinstance(payment, authorization.PaymentMandate)
    assert authorization.verified_checkout(checkout) == purchase
    assert payment.transaction_id == checkout.checkout_hash
    assert payment.payee.id == purchase["merchant_id"]
    assert payment.payment_amount.amount == purchase["amount_cents"]
    assert payment.payment_amount.currency == purchase["currency"]


@pytest.mark.student
def test_student_rejects_changed_purchase_and_mandates(purchase, mandates):
    from travel_challenge.week3 import authorization

    checkout, payment = mandates
    assert authorization.check_authorization(purchase, checkout, payment) is True
    for field, value in [("amount_cents", 999999), ("merchant_id", "other"), ("currency", "USD"), ("quote_id", "other"), ("rooms", 1)]:
        assert authorization.check_authorization({**purchase, field: value}, checkout, payment) is False
    for field, value in [("transaction_id", "other"), ("payee", {"id": "other", "name": "Other"}),
                         ("payment_amount", {"amount": 1, "currency": "SGD"}),
                         ("payment_amount", {"amount": purchase["amount_cents"], "currency": "USD"}),
                         ("payment_instrument", {"id": "other", "type": "real-card"})]:
        changed = authorization.PaymentMandate.model_validate({**payment.model_dump(), field: value})
        assert authorization.check_authorization(purchase, checkout, changed) is False
    checkout.checkout_hash = "changed"
    assert authorization.check_authorization(purchase, checkout, payment) is False