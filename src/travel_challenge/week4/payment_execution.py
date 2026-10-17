"""One simulated hotel purchase, two feedback scenarios, three Week 4 tasks."""

from copy import deepcopy
from uuid import uuid4

from travel_challenge.week3.authorization import approve_purchase, hotel_purchase, make_mandates
from travel_challenge.week1.trip_planner import make_plan


def previous_receipt(payment_id, purchase, receipts):
    """W4 task 1: absent ID -> None; identical purchase -> previous receipt.

    A stored receipt has a 'purchase' dictionary. Compare the complete purchase,
    not only its price. Conflicting details with the same ID must raise ValueError.
    Return a detached copy so callers cannot mutate the stored receipt.
    """
    raise NotImplementedError("W4 task 1: prevent duplicate or conflicting execution")


def choose_action(reason):
    """W4 task 2: TECHNICAL_ERROR -> RETRY; HOTEL_PRICE_CHANGED -> REPLAN.

    Reject any other reason with ValueError. Do not change payment IDs here.
    """
    raise NotImplementedError("W4 task 2: distinguish technical retry from replanning")


def reauthorize(purchase, *, consent):
    """W4 task 3: reuse make_mandates and approve_purchase from Week 3.

    Construct fresh mandates for the changed purchase, then pass the explicit
    consent to approve_purchase. Never return the old authorization snapshot.
    """
    raise NotImplementedError("W4 task 3: obtain new authorization after a price change")


def execute_hotel(payment_id, purchase, authorized_purchase, receipts, *, feedback="OK"):
    """Teacher execution skeleton; approved snapshots are trusted local data.

    The exact approved purchase is the only source of payment conditions: no
    separate amount/payee arguments or arbitrary payment callback are accepted.
    """
    if not isinstance(payment_id, str) or not payment_id:
        raise ValueError("A nonempty payment ID is required")
    if purchase != authorized_purchase:
        raise PermissionError("Amount, currency, merchant or purchase changed: reauthorize")
    cached = previous_receipt(payment_id, purchase, receipts)
    if cached is not None:
        return deepcopy(cached)
    if feedback == "HOTEL_PRICE_CHANGED":
        changed = deepcopy(purchase)
        changed["amount_cents"] += 5000
        changed["quote_id"] += "-SIMULATED-REPRICE"
        return {"status": "FAILED", "reason": feedback, "purchase": changed}
    if feedback not in {"OK", "TECHNICAL_ERROR"}:
        raise ValueError("Unknown execution feedback")
    receipt = {
        "status": "PAID", "mode": "SIMULATED_NO_FUNDS_MOVED",
        "payment_id": payment_id, "receipt_id": uuid4().hex,
        "purchase": deepcopy(purchase),
    }
    receipts[payment_id] = deepcopy(receipt)
    if feedback == "TECHNICAL_ERROR":
        return {"status": "FAILED", "reason": feedback}
    return receipt


def run_scenario(plan, authorized_purchase, scenario, receipts, *, consent_after_change=False):
    """Teacher walkthrough: one feedback decision and at most one further call.

    TECHNICAL_ERROR simulates a lost response AFTER a successful payment.
    HOTEL_PRICE_CHANGED simulates a new hotel quote BEFORE any payment.
    Repricing is a fixed classroom scenario, not a new Nuitee booking or planner.
    Reuse W1 make_plan after repricing. An over-budget result returns its updated
    plan with receipt=None and reason=OVER_BUDGET, before requesting approval.
    """
    if scenario not in {"TECHNICAL_ERROR", "HOTEL_PRICE_CHANGED"}:
        raise ValueError("Choose one of the two fixed scenarios")
    purchase = hotel_purchase(plan)
    updated_plan = plan
    payment_id = uuid4().hex
    first = execute_hotel(payment_id, purchase, authorized_purchase, receipts, feedback=scenario)
    action = choose_action(first["reason"])
    if action == "RETRY":
        receipt = execute_hotel(payment_id, purchase, authorized_purchase, receipts)
    elif action == "REPLAN":
        changed = first["purchase"]
        hotel = {**plan["hotel"], "id": changed["quote_id"],
                 "amount_cents": changed["amount_cents"]}
        updated_plan = make_plan(plan["request"], plan["flight"], hotel)
        if not updated_plan["within_budget"]:
            return {"first": first, "action": action, "original_payment_id": payment_id,
                    "plan": updated_plan, "receipt": None, "reason": "OVER_BUDGET"}
        authorization = reauthorize(changed, consent=consent_after_change)
        receipt = execute_hotel(uuid4().hex, changed, authorization, receipts)
    else:
        raise ValueError("Expected RETRY or REPLAN")
    return {"first": first, "action": action, "original_payment_id": payment_id,
            "plan": updated_plan, "receipt": receipt}