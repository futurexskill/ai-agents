"""ADK's equivalent of the OpenAI Agents SDK's `Runner.run(agent, prompt)`.

The OpenAI SDK's Runner is a stateless, one-line static call: give it an
agent and a string, get a result object back. ADK's Runner is
instance-based and session-oriented: it needs a session created up front,
takes the prompt as a `types.Content` object rather than a bare string,
and streams the run as an async sequence of Events instead of returning
a single result. This module wraps that ceremony once so the orchestration
script in main.py can call it the same way, three times, like the
original did with Runner.run.
"""

import uuid

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

APP_NAME = "stock_monitor"


async def run_agent(
    agent: Agent,
    prompt: str,
    session_service: InMemorySessionService,
    user_id: str,
) -> str:
    """Runs one agent on one prompt and returns its final text output."""
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)

    return final_text
