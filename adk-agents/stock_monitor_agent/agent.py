"""The three-agent architecture, ported from multi_agent_openai.py.

Same three roles, same instructions, same 50/75/120-word constraints.
What changed to fit ADK's Agent (= LlmAgent):
  - `instructions=` -> `instruction=` (singular).
  - `name` must be a valid Python identifier, so "Price Analyst" etc.
    become snake_case; the human-readable name moves to `description`.
  - `model="gpt-5.5"` -> a Gemini model id, since ADK's native model
    integration is Gemini. (To keep calling OpenAI models instead, swap
    in `google.adk.models.lite_llm.LiteLlm(model="gpt-5.5")` as `model=`.)
"""

from google.adk.agents import Agent

MODEL = "gemini-2.5-flash"

price_agent = Agent(
    name="price_analyst",
    model=MODEL,
    description="Price Analyst",
    instruction="""
Analyze stock price movements.
Explain whether the movement is significant.
Keep your answer under 50 words.
""",
)

news_agent = Agent(
    name="news_researcher",
    model=MODEL,
    description="News Researcher",
    instruction="""
Search for possible reasons behind today's stock movement.
Summarize recent news in under 75 words.
""",
)

summary_agent = Agent(
    name="investment_summary",
    model=MODEL,
    description="Investment Summary",
    instruction="""
Combine multiple analyses into a professional email.

Keep the response under 120 words.
""",
)
