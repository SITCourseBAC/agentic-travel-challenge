"""Week 1 student functions, reused unchanged by the Week 2 agents."""

from copy import deepcopy
from datetime import date
from decimal import Decimal

from travel_challenge.config import trip_scenario


def get_trip_request():
    """Teacher setup: validate the scenario and return a detached request in cents."""
    request = deepcopy(trip_scenario.TRIP)

    if request["travellers"] <= 0:
        raise ValueError("travellers must be positive")
    for adults in request["adults_per_room"]:
        if adults <= 0:
            raise ValueError("Each room must contain a positive number of adults")
    if sum(request["adults_per_room"]) != request["travellers"]:
        raise ValueError("Room occupants must add up to travellers")
    if request["currency"] != "SGD":
        raise ValueError("This lab supports SGD pricing only")

    departure = date.fromisoformat(request["departure_date"])
    return_date = date.fromisoformat(request["return_date"])
    if return_date <= departure:
        raise ValueError("return_date must be after departure_date (YYYY-MM-DD)")

    budget_cents = Decimal(str(request.pop("budget_sgd"))) * 100
    if not budget_cents.is_finite() or budget_cents <= 0:
        raise ValueError("budget_sgd must be positive and finite")
    if budget_cents != budget_cents.to_integral_value():
        raise ValueError("budget_sgd must have no more than two decimal places")
    request["budget_cents"] = int(budget_cents)
    return request


def hotel_occupancies(adults_per_room):
    """W1 task 1: convert room adult counts into Nuitee occupancy dictionaries.

    Input [1, 1] means two single rooms; [2, 1] means a double and a single.
    Return one dictionary with an 'adults' field per room. Teacher setup checks
    that the configured room occupants add up to the traveller count.
    """
    raise NotImplementedError("W1: build the room occupancy list")


def normalize_flights(payload, request):
    """W1 task 2: return quotes with id, amount_cents, currency, duration_minutes.

    Each data group contains journeys. Use each journey's cheapestOffer.offerId,
    cheapestOffer.pricing.display.total/currency, and totalDuration.minutes.
    The total already covers all travellers and both legs; do not multiply it.
    Convert amounts to integer cents and reject a currency different from request.
    Missing required fields must fail visibly, not become invented prices.
    """
    quotes = []
    for group in payload["data"]:
        for journey in group["journeys"]:
            offer = journey["cheapestOffer"]
            quote_id = offer["offerId"]
            raise NotImplementedError("W1: extract flight currency, cents and duration; append a quote")
    return quotes


def normalize_hotels(payload, request):
    """W1 task 2: return id, merchant_id, merchant_name, amount_cents, currency, rooms.

    data contains hotelId and roomTypes. Each room type has offerId and
    offerRetailRate.amount/currency. Match hotelId to hotels[].id for the name.
    offerRetailRate already covers all requested rooms and the complete stay.
    Set rooms to len(request['adults_per_room']); NEVER multiply this total again.
    Convert amounts to integer cents and reject a currency different from request.
    """
    quotes = []
    for hotel in payload["data"]:
        for offer in hotel["roomTypes"]:
            raise NotImplementedError("W1: match hotel name, extract currency and cents; append a quote")
    return quotes


def choose_option(options):
    """W1 task 3: return the lowest amount_cents quote; reject an empty list."""
    raise NotImplementedError("W1: select the cheapest available quote")


def make_plan(request, flight, hotel):
    """W1 task 4: return request, flight, hotel, total_cents, within_budget.

    Require both quote currencies to match request['currency']. Add the two
    already-complete totals; within_budget compares against budget_cents.
    Preserve the original quote dictionaries, including the supplier IDs.
    """
    raise NotImplementedError("W1: assemble the plan and check the total budget")