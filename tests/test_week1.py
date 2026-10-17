"""Teacher checks: -m scaffold. Student acceptance checks: -m student."""

import subprocess
import sys

import httpx
import pytest

from travel_challenge.week1 import nuitee_rest, trip_planner


@pytest.fixture
def trip():
    return {"origin": "SIN", "airport": "NRT", "city": "Tokyo",
            "departure_date": "2027-03-20", "return_date": "2027-03-23",
            "travellers": 5, "adults_per_room": [1, 1, 1, 1, 1], "hotel_country": "JP",
            "currency": "SGD", "budget_cents": 700000,
            "flight_cabin_class": "ECONOMY", "flight_country": "SG",
            "hotel_guest_nationality": "SG", "hotel_search_limit": 5,
            "hotel_max_rates_per_hotel": 1}


@pytest.mark.scaffold
def test_week1_imports_without_protocols():
    result = subprocess.run([sys.executable, "-c", (
        "import sys; from travel_challenge.week1 import nuitee_rest, trip_planner; "
        "assert not any(n.startswith(('a2a', 'mcp', 'x402', 'ap2')) for n in sys.modules)"
    )], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.scaffold
@pytest.mark.parametrize("kind", ["flights", "hotels"])
def test_real_rest_request_contract(monkeypatch, trip, kind):
    monkeypatch.setenv("NUITEE_API_KEY", "test-only-not-a-real-key")
    captured = {}
    payload = {"data": [{"test": "raw provider response"}]}

    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(nuitee_rest.httpx, "post", post)
    if kind == "flights":
        assert nuitee_rest.search_flights(trip) == payload
        assert captured["json"]["adults"] == 5
        assert captured["json"]["legs"] == [
            {"origin": "SIN", "destination": "NRT", "date": "2027-03-20", "direction": "OUTBOUND"},
            {"origin": "NRT", "destination": "SIN", "date": "2027-03-23", "direction": "INBOUND"},
        ]
    else:
        rooms = [{"adults": 1}] * 5
        assert nuitee_rest.search_hotels(trip, rooms) == payload
        assert captured["json"]["occupancies"] == rooms
        assert captured["json"]["checkin"] == trip["departure_date"]
        assert captured["json"]["checkout"] == trip["return_date"]
    assert captured["url"] == f"https://api.liteapi.travel/v3.0/{kind}/rates"
    assert captured["json"]["currency"] == "SGD"
    assert captured["headers"]["X-API-Key"] == "test-only-not-a-real-key"


@pytest.mark.scaffold
def test_missing_key_and_http_failure_are_visible(monkeypatch, trip):
    monkeypatch.setattr(nuitee_rest, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("NUITEE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="NUITEE_API_KEY"):
        nuitee_rest.search_flights(trip)
    monkeypatch.setenv("NUITEE_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setattr(nuitee_rest.httpx, "post", lambda *args, **kwargs: httpx.Response(
        401, request=httpx.Request("POST", "https://test"),
    ))
    with pytest.raises(httpx.HTTPStatusError):
        nuitee_rest.search_flights(trip)


@pytest.mark.student
def test_single_room_occupancy():
    assert trip_planner.hotel_occupancies([1, 1, 1, 1, 1]) == [{"adults": 1}] * 5
    assert trip_planner.hotel_occupancies([2, 2, 1]) == [{"adults": 2}, {"adults": 2}, {"adults": 1}]


@pytest.fixture
def raw_flights():
    return {"data": [{"journeys": [{
        "cheapestOffer": {"offerId": "flight-offer-1", "pricing": {"display": {
            "total": 3912.26, "currency": "SGD",
        }}}, "totalDuration": {"minutes": 860},
    }]}]}


@pytest.fixture
def raw_hotels():
    return {"hotels": [{"id": "hotel-1", "name": "Test Hotel"}], "data": [{
        "hotelId": "hotel-1", "roomTypes": [{
            "offerId": "hotel-offer-1", "offerRetailRate": {"amount": 3015.29, "currency": "SGD"},
        }],
    }]}


@pytest.mark.student
def test_flight_normalization_keeps_group_round_trip_total(trip, raw_flights):
    quotes = trip_planner.normalize_flights(raw_flights, trip)
    assert len(quotes) == 1
    assert quotes[0]["id"] == "flight-offer-1"
    assert quotes[0]["amount_cents"] == 391226
    assert type(quotes[0]["amount_cents"]) is int
    assert quotes[0]["currency"] == "SGD"
    assert quotes[0]["duration_minutes"] == 860


@pytest.mark.student
def test_hotel_normalization_keeps_all_rooms_full_stay_total(trip, raw_hotels):
    quotes = trip_planner.normalize_hotels(raw_hotels, trip)
    assert len(quotes) == 1
    quote = quotes[0]
    assert quote["id"] == "hotel-offer-1"
    assert quote["merchant_id"] == "hotel-1"
    assert quote["merchant_name"] == "Test Hotel"
    assert quote["amount_cents"] == 301529
    assert type(quote["amount_cents"]) is int
    assert quote["rooms"] == 5
    assert quote["currency"] == "SGD"


@pytest.mark.student
@pytest.mark.parametrize("kind", ["flights", "hotels"])
def test_normalizers_reject_other_currency(trip, raw_flights, raw_hotels, kind):
    if kind == "flights":
        raw_flights["data"][0]["journeys"][0]["cheapestOffer"]["pricing"]["display"]["currency"] = "USD"
        normalize, payload = trip_planner.normalize_flights, raw_flights
    else:
        raw_hotels["data"][0]["roomTypes"][0]["offerRetailRate"]["currency"] = "USD"
        normalize, payload = trip_planner.normalize_hotels, raw_hotels
    with pytest.raises(ValueError):
        normalize(payload, trip)


@pytest.mark.student
def test_choose_cheapest_and_reject_empty():
    options = [{"id": "expensive", "amount_cents": 2100}, {"id": "cheap", "amount_cents": 2000}]
    assert trip_planner.choose_option(options) == options[1]
    with pytest.raises(ValueError):
        trip_planner.choose_option([])


@pytest.mark.student
def test_plan_counts_once_checks_budget_and_currency(trip):
    flight = {"id": "flight-1", "amount_cents": 338012, "currency": "SGD"}
    hotel = {"id": "hotel-1", "amount_cents": 302010, "currency": "SGD", "rooms": 5}
    assert trip["budget_cents"] == 700000
    assert trip_planner.make_plan(trip, flight, hotel)["within_budget"] is True
    trip["budget_cents"] = 640022
    plan = trip_planner.make_plan(trip, flight, hotel)
    assert plan["request"] == trip
    assert plan["flight"] == flight and plan["hotel"] == hotel
    assert plan["total_cents"] == 640022
    assert type(plan["total_cents"]) is int
    assert plan["within_budget"] is True
    trip["budget_cents"] -= 1
    assert trip_planner.make_plan(trip, flight, hotel)["within_budget"] is False
    with pytest.raises(ValueError):
        trip_planner.make_plan(trip, flight, {**hotel, "currency": "USD"})