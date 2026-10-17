"""Small teacher execution checks and three student tasks, with both scenarios."""

from copy import deepcopy

import pytest

from travel_challenge.week3 import authorization
from travel_challenge.week4 import payment_execution as execution


@pytest.fixture
def purchase():
    return {"quote_id": "test-offer", "merchant_id": "test-hotel", "merchant_name": "Test Hotel",
            "amount_cents": 302010, "currency": "SGD", "rooms": 5,
            "checkin": "2027-03-20", "checkout": "2027-03-23"}


@pytest.fixture
def plan(purchase):
    return {
        "request": {"departure_date": purchase["checkin"], "return_date": purchase["checkout"],
                    "currency": "SGD", "budget_cents": 700000, "travellers": 5},
        "flight": {"id": "test-flight", "amount_cents": 338012, "currency": "SGD"},
        "hotel": {"id": purchase["quote_id"], "merchant_id": purchase["merchant_id"],
                  "merchant_name": purchase["merchant_name"], "amount_cents": purchase["amount_cents"],
                  "currency": purchase["currency"], "rooms": purchase["rooms"]},
        "total_cents": 640022, "within_budget": True,
    }


@pytest.mark.scaffold
def test_execution_binds_every_approved_condition(purchase):
    for field, value in [("amount_cents", 1), ("currency", "USD"), ("merchant_id", "other"),
                         ("quote_id", "other"), ("rooms", 1), ("checkin", "2027-03-21")]:
        with pytest.raises(PermissionError):
            execution.execute_hotel("test-payment", {**purchase, field: value}, purchase, {})
    with pytest.raises(ValueError):
        execution.execute_hotel("", purchase, purchase, {})


@pytest.mark.scaffold
def test_fixed_feedback_records_only_the_completed_payment(monkeypatch, purchase):
    monkeypatch.setattr(execution, "previous_receipt", lambda *args: None)
    receipts = {}
    lost = execution.execute_hotel("lost-response", purchase, deepcopy(purchase), receipts, feedback="TECHNICAL_ERROR")
    assert lost == {"status": "FAILED", "reason": "TECHNICAL_ERROR"}
    assert receipts["lost-response"]["purchase"] == purchase
    assert receipts["lost-response"]["mode"] == "SIMULATED_NO_FUNDS_MOVED"
    changed = execution.execute_hotel("repriced", purchase, deepcopy(purchase), receipts, feedback="HOTEL_PRICE_CHANGED")
    assert changed["purchase"]["amount_cents"] == purchase["amount_cents"] + 5000
    assert changed["purchase"]["quote_id"] != purchase["quote_id"]
    assert "repriced" not in receipts
    stored = deepcopy(receipts["lost-response"])
    monkeypatch.setattr(execution, "previous_receipt", lambda *args: stored)
    again = execution.execute_hotel("lost-response", purchase, deepcopy(purchase), receipts)
    assert again == stored
    assert receipts == {"lost-response": stored}


@pytest.mark.scaffold
@pytest.mark.parametrize("scenario,action", [("TECHNICAL_ERROR", "RETRY"), ("HOTEL_PRICE_CHANGED", "REPLAN")])
def test_teacher_skeleton_preserves_ids_and_requests_new_authorization(monkeypatch, purchase, plan, scenario, action):
    calls = []
    changed = {**purchase, "amount_cents": purchase["amount_cents"] + 5000, "quote_id": "repriced-test-offer"}
    updated = deepcopy(plan)
    updated["hotel"].update(id=changed["quote_id"], amount_cents=changed["amount_cents"])
    updated["total_cents"] += 5000
    plan_calls = []

    def replan(request, flight, hotel):
        assert request == plan["request"] and flight == plan["flight"]
        assert hotel == updated["hotel"]
        plan_calls.append("make_plan")
        return updated

    def execute(payment_id, actual, approved, receipts, *, feedback="OK"):
        calls.append((payment_id, actual, approved))
        if feedback != "OK":
            return {"status": "FAILED", "reason": scenario, "purchase": changed}
        assert actual == approved
        return {"status": "PAID", "payment_id": payment_id}

    def reauthorize(actual, *, consent):
        assert actual == changed and consent is True
        return deepcopy(changed)

    monkeypatch.setattr(execution, "execute_hotel", execute)
    monkeypatch.setattr(execution, "choose_action", lambda reason: action)
    monkeypatch.setattr(execution, "reauthorize", reauthorize)
    monkeypatch.setattr(execution, "make_plan", replan)
    result = execution.run_scenario(plan, deepcopy(purchase), scenario, {}, consent_after_change=True)
    assert result["action"] == action
    assert len(calls) == 2
    if action == "RETRY":
        assert calls[0][0] == calls[1][0]
        assert calls[1][1] == purchase
        assert plan_calls == []
        assert result["plan"] == plan
    else:
        assert calls[0][0] != calls[1][0]
        assert calls[1][1] == changed
        assert plan_calls == ["make_plan"]
        assert result["plan"] == updated


@pytest.mark.scaffold
@pytest.mark.parametrize("headroom,within_budget", [(4999, False), (5000, True)])
def test_reprice_checks_trip_budget_before_authorization(monkeypatch, purchase, plan, headroom, within_budget):
    plan["request"]["budget_cents"] = plan["total_cents"] + headroom
    original = deepcopy(plan)
    updated = deepcopy(plan)
    updated["hotel"]["amount_cents"] += 5000
    updated["hotel"]["id"] += "-SIMULATED-REPRICE"
    updated["total_cents"] += 5000
    updated["within_budget"] = within_budget
    calls = []

    def replan(request, flight, hotel):
        assert request == plan["request"] and flight == plan["flight"]
        assert hotel == updated["hotel"]
        calls.append("budget")
        return updated

    def approve(changed, *, consent):
        assert within_budget and consent is True
        assert changed == authorization.hotel_purchase(updated)
        calls.append("authorization")
        return deepcopy(changed)

    monkeypatch.setattr(execution, "previous_receipt", lambda *args: None)
    monkeypatch.setattr(execution, "choose_action", lambda reason: "REPLAN")
    monkeypatch.setattr(execution, "make_plan", replan)
    monkeypatch.setattr(execution, "reauthorize", approve)
    receipts = {}
    result = execution.run_scenario(plan, deepcopy(purchase), "HOTEL_PRICE_CHANGED", receipts,
                                    consent_after_change=True)
    assert result["plan"] == updated
    assert plan == original
    if within_budget:
        assert calls == ["budget", "authorization"]
        assert len(receipts) == 1
        assert result["receipt"]["purchase"] == authorization.hotel_purchase(updated)
        assert result["receipt"]["payment_id"] != result["original_payment_id"]
    else:
        assert calls == ["budget"]
        assert result["receipt"] is None and result["reason"] == "OVER_BUDGET"
        assert not receipts


@pytest.mark.student
def test_previous_receipt_rejects_conflicts_and_returns_detached_copy(purchase):
    assert execution.previous_receipt("payment-1", purchase, {}) is None
    receipts = {"payment-1": {"purchase": deepcopy(purchase), "receipt_id": "receipt-1", "status": "PAID"}}
    cached = execution.previous_receipt("payment-1", purchase, receipts)
    assert cached == receipts["payment-1"]
    cached["purchase"]["amount_cents"] = 1
    assert receipts["payment-1"]["purchase"] == purchase
    for field, value in [("amount_cents", 1), ("currency", "USD"), ("merchant_id", "other"), ("quote_id", "other")]:
        with pytest.raises(ValueError):
            execution.previous_receipt("payment-1", {**purchase, field: value}, receipts)


@pytest.mark.student
def test_retry_or_replan_decision():
    assert execution.choose_action("TECHNICAL_ERROR") == "RETRY"
    assert execution.choose_action("HOTEL_PRICE_CHANGED") == "REPLAN"
    with pytest.raises(ValueError):
        execution.choose_action("UNKNOWN")


@pytest.mark.student
def test_reauthorization_reuses_week3_and_requires_consent(monkeypatch, purchase):
    checkout, payment = object(), object()
    calls = []

    def make(actual):
        assert actual == purchase
        calls.append("make")
        return checkout, payment

    def approve(actual, actual_checkout, actual_payment, *, consent):
        assert actual == purchase and actual_checkout is checkout and actual_payment is payment
        calls.append("approve")
        if consent is not True:
            raise PermissionError("Approval required")
        return deepcopy(purchase)

    monkeypatch.setattr(execution, "make_mandates", make)
    monkeypatch.setattr(execution, "approve_purchase", approve)
    assert execution.reauthorize(purchase, consent=True) == purchase
    assert calls == ["make", "approve"]
    with pytest.raises(PermissionError):
        execution.reauthorize(purchase, consent=False)


@pytest.mark.student
def test_lost_response_retries_same_id_without_second_receipt(purchase, plan):
    receipts = {}
    snapshot = deepcopy(purchase)
    result = execution.run_scenario(plan, snapshot, "TECHNICAL_ERROR", receipts)
    assert result["action"] == "RETRY"
    assert result["receipt"]["payment_id"] == result["original_payment_id"]
    assert len(receipts) == 1
    assert execution.execute_hotel(result["original_payment_id"], purchase, snapshot, receipts) == result["receipt"]


@pytest.mark.student
def test_price_change_requires_new_approval_and_new_id(purchase, plan):
    checkout, payment = authorization.make_mandates(purchase)
    snapshot = authorization.approve_purchase(purchase, checkout, payment, consent=True)
    receipts = {}
    with pytest.raises(PermissionError):
        execution.run_scenario(plan, snapshot, "HOTEL_PRICE_CHANGED", receipts, consent_after_change=False)
    assert not receipts
    result = execution.run_scenario(plan, snapshot, "HOTEL_PRICE_CHANGED", receipts, consent_after_change=True)
    assert result["action"] == "REPLAN"
    assert result["receipt"]["payment_id"] != result["original_payment_id"]
    changed = result["receipt"]["purchase"]
    assert changed["amount_cents"] == purchase["amount_cents"] + 5000
    assert changed["quote_id"] != purchase["quote_id"]
    assert result["plan"]["hotel"]["id"] == changed["quote_id"]
    assert result["plan"]["total_cents"] == plan["total_cents"] + 5000
    assert result["plan"]["within_budget"] is True
    assert len(receipts) == 1
    with pytest.raises(PermissionError):
        execution.execute_hotel("another-id", changed, snapshot, receipts)
    over_hotel = {**plan["hotel"], "id": "over-budget-offer",
                  "amount_cents": plan["hotel"]["amount_cents"] + 70000}
    over_plan = execution.make_plan(plan["request"], plan["flight"], over_hotel)
    assert over_plan["request"]["budget_cents"] == 700000
    assert over_plan["total_cents"] == 710022 and not over_plan["within_budget"]
    with pytest.raises(ValueError, match="within budget"):
        authorization.hotel_purchase(over_plan)
    assert len(receipts) == 1