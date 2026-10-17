"""Instructor-owned A2A server registration and task lifecycle."""

import json

from a2a.helpers import (
    get_message_text, new_task_from_user_message, new_text_message, new_text_part,
)
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette


class QuoteExecutor(AgentExecutor):
    """Translate an SDK task into one ordinary quote function call."""

    def __init__(self, business_handler):
        self.business_handler = business_handler

    async def execute(self, context, event_queue):
        task = new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        try:
            request = json.loads(get_message_text(context.message))
            quote = await self.business_handler(request)
            await updater.add_artifact([new_text_part(json.dumps(quote))])
            await updater.complete()
        except Exception as error:
            await updater.failed(new_text_message(f"{type(error).__name__}: {error}"))

    async def cancel(self, context, event_queue):
        raise NotImplementedError("This lab only uses blocking quote requests.")


def agent_app(name, url, business_handler):
    card = AgentCard(
        name=name, description=f"{name} travel quotes", version="1.0.0",
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[AgentInterface(
            protocol_binding="JSONRPC", url=url + "/", protocol_version="1.0",
        )],
        skills=[AgentSkill(id=name.lower(), name=name, description="Select a quote",
                           tags=["travel"])],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=QuoteExecutor(business_handler), task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card)
    routes.extend(create_jsonrpc_routes(request_handler, "/"))
    return Starlette(routes=routes)