"""Instructor-provided MCP server: exactly two real Nuitee search tools."""

from typing import Any

from mcp.server import MCPServer

from travel_challenge.week1 import nuitee_rest


mcp = MCPServer("Travel search")


@mcp.tool(structured_output=True)
def search_flights(request: dict[str, Any]) -> dict[str, Any]:
    """Find round-trip quotes for all travellers using real Nuitee REST."""
    return nuitee_rest.search_flights(request)


@mcp.tool(structured_output=True)
def search_hotels(request: dict[str, Any], occupancies: list[dict[str, Any]]) -> dict[str, Any]:
    """Find full-stay quotes for all requested rooms using real Nuitee REST."""
    return nuitee_rest.search_hotels(request, occupancies)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8010,
            stateless_http=True, json_response=True)