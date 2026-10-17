"""Real SDK transport checks and separate unfinished student acceptance checks."""

import asyncio
import json

import httpx
import pytest
from mcp import Client
from starlette.applications import Starlette
from starlette.routing import Mount

from travel_challenge.week2 import a2a_coordinator, travel_agents
from travel_challenge.week1 import nuitee_rest
from travel_challenge.week2.mcp_tools import mcp


@pytest.mark.scaffold
@pytest.mark.parametrize("kind", ["flights", "hotels"])
def test_official_a2a_mcp_rest_round_trip(monkeypatch, kind):
    captured = {}
    payload = {"data": [{"probe": "test-only supplier response"}]}

    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setenv("NUITEE_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setattr(nuitee_rest.httpx, "post", post)

    async def probe(request):
        arguments = {"request": request}
        if kind == "hotels":
            arguments["occupancies"] = [{"adults": 1}] * 5
        async with Client(mcp) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {"search_flights", "search_hotels"}
            result = await client.call_tool(f"search_{kind}", arguments)
            assert not result.is_error
            return result.structured_content

    async def run():
        url = f"http://test/{kind}"
        app = Starlette(routes=[Mount(f"/{kind}", app=a2a_coordinator.agent_app(kind, url, probe))])
        request = {"origin": "SIN", "airport": "NRT", "city": "Tokyo",
                   "departure_date": "2027-03-20", "return_date": "2027-03-23",
                   "travellers": 5, "hotel_country": "JP", "currency": "SGD",
                   "flight_cabin_class": "ECONOMY", "flight_country": "SG",
                   "hotel_guest_nationality": "SG", "hotel_search_limit": 5,
                   "hotel_max_rates_per_hotel": 1}
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport) as client:
            card = (await client.get(url + "/.well-known/agent-card.json")).json()
            assert card["capabilities"]["streaming"] is False
        message = a2a_coordinator.SendMessageRequest(message=a2a_coordinator.new_text_message(
            json.dumps(request), role=a2a_coordinator.Role.ROLE_USER,
        ))
        assert await a2a_coordinator.send_task(url, message, transport=transport) == payload

    asyncio.run(run())
    assert captured["url"].endswith(f"/{kind}/rates")
    if kind == "hotels":
        assert captured["json"]["occupancies"] == [{"adults": 1}] * 5


@pytest.mark.scaffold
def test_a2a_task_failure_reaches_caller():
    async def reject(request):
        raise ValueError("quote unavailable")

    async def run():
        app = a2a_coordinator.agent_app("Reject", "http://test", reject)
        message = a2a_coordinator.SendMessageRequest(message=a2a_coordinator.new_text_message(
            "{}", role=a2a_coordinator.Role.ROLE_USER,
        ))
        with pytest.raises(RuntimeError, match="quote unavailable"):
            await a2a_coordinator.send_task("http://test", message, transport=httpx.ASGITransport(app=app))

    asyncio.run(run())


@pytest.mark.student
@pytest.mark.parametrize("kind", ["flights", "hotels"])
def test_specialists_reuse_week1_functions(monkeypatch, kind):
    request = {"travellers": 5, "adults_per_room": [1, 1, 1, 1, 1]}
    raw = {"data": [{"probe": kind}]}
    normalized = [{"id": f"{kind}-quote", "amount_cents": 100, "currency": "SGD"}]
    calls = []

    def normalize(payload, actual_request):
        assert payload == raw and actual_request == request
        calls.append("normalize")
        return normalized

    def choose(options):
        assert options == normalized
        calls.append("choose")
        return normalized[0]

    def search(actual_request, *occupancies):
        assert actual_request == request
        if kind == "hotels":
            assert occupancies == ([{"adults": 1}] * 5,)
        calls.append("tool")
        return raw

    monkeypatch.setattr(travel_agents, "MCP_URL", mcp)
    monkeypatch.setattr(nuitee_rest, f"search_{kind}", search)
    monkeypatch.setattr(travel_agents, f"normalize_{kind}", normalize)
    monkeypatch.setattr(travel_agents, "choose_option", choose)
    monkeypatch.setattr(travel_agents, "hotel_occupancies", lambda rooms: [{"adults": 1}] * 5)
    agent = travel_agents.flight_agent if kind == "flights" else travel_agents.hotel_agent
    assert asyncio.run(agent(request)) == normalized[0]
    assert calls == ["tool", "normalize", "choose"]


@pytest.mark.student
def test_coordinator_calls_both_specialists_and_shared_plan(monkeypatch):
    request = {"currency": "SGD", "budget_cents": 1000}
    calls = []
    quotes = {a2a_coordinator.FLIGHT_URL: {"id": "flight"},
              a2a_coordinator.HOTEL_URL: {"id": "hotel"}}

    async def send(url, message):
        assert isinstance(message, a2a_coordinator.SendMessageRequest)
        assert message.message.role == a2a_coordinator.Role.ROLE_USER
        assert json.loads(a2a_coordinator.get_message_text(message.message)) == request
        calls.append(url)
        return quotes[url]

    def combine(actual_request, flight, hotel):
        assert actual_request == request
        assert flight == {"id": "flight"} and hotel == {"id": "hotel"}
        calls.append("make_plan")
        return {"probe": "shared W1 make_plan was called"}

    monkeypatch.setattr(a2a_coordinator, "send_task", send)
    monkeypatch.setattr(a2a_coordinator, "make_plan", combine)
    assert asyncio.run(a2a_coordinator.plan_trip(request)) == {"probe": "shared W1 make_plan was called"}
    assert set(calls[:2]) == set(quotes)
    assert calls[2:] == ["make_plan"]