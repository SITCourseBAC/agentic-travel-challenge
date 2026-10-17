"""Visible official A2A client calls and the Week 2 student coordinator."""

import json

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_message_text, new_text_message
from a2a.types import Role, SendMessageRequest, TaskState

from travel_challenge.sdk_support.a2a_server import agent_app
from travel_challenge.week1.trip_planner import make_plan


FLIGHT_URL = "http://127.0.0.1:8001/flights"
HOTEL_URL = "http://127.0.0.1:8001/hotels"


async def send_task(url, message, *, transport=None):
    """Teacher transport: send an official SendMessageRequest and read its artifact."""
    async with httpx.AsyncClient(timeout=90, transport=transport) as http:
        card = await A2ACardResolver(httpx_client=http, base_url=url).get_agent_card()
        client = await create_client(
            agent=card, client_config=ClientConfig(streaming=False, httpx_client=http),
        )
        try:
            async for response in client.send_message(message):
                if response.HasField("task"):
                    task = response.task
                    if task.status.state != TaskState.TASK_STATE_COMPLETED:
                        raise RuntimeError(get_message_text(task.status.message))
                    quote_text = task.artifacts[0].parts[0].text
                    return json.loads(quote_text)
        finally:
            await client.close()
    raise RuntimeError("Agent returned no quote artifact")


async def plan_trip(request):
    """W2 task 3: replace message = None with an official SendMessageRequest.

    Its message field uses new_text_message with json.dumps(request) and
    role=Role.ROLE_USER. The teacher sends it to both specialists, reads their
    quote artifacts and reuses W1 make_plan. Do not duplicate pricing logic.
    """
    message = None
    if message is None:
        raise NotImplementedError("W2 task 3: construct the official A2A request message")
    flight = await send_task(FLIGHT_URL, message)
    hotel = await send_task(HOTEL_URL, message)
    return make_plan(request, flight, hotel)