"""Official AP2 models plus two Week 3 student tasks; no full AP2 trust chain."""

from copy import deepcopy

from ap2.sdk.generated.checkout_mandate import CheckoutMandate
from ap2.sdk.generated.payment_mandate import PaymentMandate
from travel_challenge.sdk_support.ap2_signing import (
    checkout_hash, signed_checkout, verified_checkout,
)


def hotel_purchase(plan):
    """Use the existing W1/W2 plan, never another planner or a fabricated quote."""
    if plan["within_budget"] is not True:
        raise ValueError("Approve only a trip that is within budget")
    hotel, request = plan["hotel"], plan["request"]
    if hotel["currency"] != request["currency"]:
        raise ValueError("Hotel and trip currencies differ")
    if type(hotel["amount_cents"]) is not int or hotel["amount_cents"] <= 0:
        raise ValueError("Hotel amount must be positive integer cents")
    return {
        "quote_id": hotel["id"], "merchant_id": hotel["merchant_id"],
        "merchant_name": hotel["merchant_name"],
        "amount_cents": hotel["amount_cents"], "currency": hotel["currency"],
        "rooms": hotel["rooms"], "checkin": request["departure_date"],
        "checkout": request["return_date"],
    }


def make_mandates(purchase):
    """W3 task 3: return official (CheckoutMandate, PaymentMandate) objects.

    Use token/binding for checkout_jwt/checkout_hash and transaction_id.
    Payment payee is {id: merchant_id, name: merchant_name}; payment_amount is
    {amount: amount_cents, currency: currency}. Use payment_instrument
    {id: 'course-card', type: 'simulated'}. No real card or bank account is used.
    """
    token, binding = signed_checkout(purchase)
    raise NotImplementedError("W3 task 3: populate the two official AP2 models")


def check_authorization(purchase, checkout, payment):
    """W3 task 4: return True only for an unchanged, matching hotel purchase.

    Require verified_checkout(checkout) == purchase, matching transaction_id,
    merchant id/name, amount, currency and the supplied simulated instrument.
    Return False for changed conditions or invalid checkout verification.
    Official model validation checks structure; these are local business checks.
    """
    raise NotImplementedError("W3 task 4: compare the purchase and official mandates")


def approve_purchase(purchase, checkout, payment, *, consent):
    """Explicit classroom consent plus student checks produce a detached snapshot.

    The snapshot is trusted in-process teaching data, not a signed user credential.
    Neither the user mandate nor a full AP2 credential chain is verified here.
    """
    if consent is not True:
        raise PermissionError("Human approval is required")
    if not check_authorization(purchase, checkout, payment):
        raise PermissionError("Purchase does not match the AP2 mandates")
    return deepcopy(purchase)