"""Two A2A specialists in one process; MCP transport is provided by the teacher."""

from mcp import Client
from starlette.applications import Starlette
from starlette.routing import Mount

from travel_challenge.week2.a2a_coordinator import FLIGHT_URL, HOTEL_URL, agent_app
from travel_challenge.week1.trip_planner import (
    choose_option, hotel_occupancies, normalize_flights, normalize_hotels,
)


MCP_URL = "http://127.0.0.1:8010/mcp"


async def flight_agent(request):
    """W2 task 1: replace result = None with the official MCP tool invocation.

    Await client.call_tool using tool 'search_flights' and arguments containing
    the original request under 'request'. Inspect structured_content below.
    The teacher reuses W1 normalization and selection after your SDK call.
    """
    async with Client(MCP_URL) as client:
        result = None
        if result is None:
            raise NotImplementedError("W2 task 1: call the official MCP search_flights tool")
        if result.is_error:
            raise RuntimeError(f"MCP flight search failed: {result.content}")
        raw = result.structured_content
    return choose_option(normalize_flights(raw, request))


async def hotel_agent(request):
    """Receive a request dictionary; return the hotel quote selected by W1."""
    async with Client(MCP_URL) as client:
        result = await client.call_tool("search_hotels", {
            "request": request, "occupancies": hotel_occupancies(request["adults_per_room"]),
        })
        if result.is_error:
            raise RuntimeError(f"MCP hotel search failed: {result.content}")
        raw = result.structured_content
    raise NotImplementedError("W2 task 2: reuse normalize_hotels and choose_option on raw")


app = Starlette(routes=[
    Mount("/flights", app=agent_app("Flight", FLIGHT_URL, flight_agent)),
    Mount("/hotels", app=agent_app("Hotel", HOTEL_URL, hotel_agent)),
])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)