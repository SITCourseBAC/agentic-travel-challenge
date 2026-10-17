"""Real Nuitee REST requests; no agent or payment SDK is imported here."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


def _post(endpoint, payload):
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
    api_key = os.environ.get("NUITEE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise RuntimeError("Set NUITEE_API_KEY in .env or your environment before searching.")
    response = httpx.post(
        f"https://api.liteapi.travel/v3.0/{endpoint}",
        headers={"X-API-Key": api_key, "Accept": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def search_flights(request):
    """Return raw round-trip offers for every traveller, in the requested currency."""
    return _post("flights/rates", {
        "legs": [
            {"origin": request["origin"], "destination": request["airport"],
             "date": request["departure_date"], "direction": "OUTBOUND"},
            {"origin": request["airport"], "destination": request["origin"],
             "date": request["return_date"], "direction": "INBOUND"},
        ],
        "adults": request["travellers"],
        "currency": request["currency"],
        "cabinClass": request["flight_cabin_class"],
        "country": request["flight_country"],
    })


def search_hotels(request, occupancies):
    """Return raw offers; offerRetailRate covers ALL requested rooms and nights."""
    return _post("hotels/rates", {
        "cityName": request["city"],
        "countryCode": request["hotel_country"],
        "checkin": request["departure_date"],
        "checkout": request["return_date"],
        "occupancies": occupancies,
        "currency": request["currency"],
        "guestNationality": request["hotel_guest_nationality"],
        "limit": request["hotel_search_limit"],
        "maxRatesPerHotel": request["hotel_max_rates_per_hotel"],
        "includeHotelData": True,
    })