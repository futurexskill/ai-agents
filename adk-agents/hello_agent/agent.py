from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="hello_agent",
    model="gemini-2.5-flash",
    description="A simple hello world agent.",
    instruction="You are a friendly assistant. Greet the user warmly and answer their questions concisely. Use the google_search tool for questions about current events, real-time data, or anything requiring up-to-date information.",
    tools=[google_search],
)
