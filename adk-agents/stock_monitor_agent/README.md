# Stock Monitor Agent

An ADK port of `multi_agent_openai.py` — a three-agent pipeline that pulls a
stock's latest price move, has one agent analyze the price action, another
research likely causes, a third write an investment summary, and then emails
the result. The architecture, prompts, and word-count constraints are
unchanged from the original; only the SDK underneath is different.

## Architecture

```
get_stock_info(ticker)          [tools.py — Yahoo Finance, unchanged]
        |
        v
  price_agent   ──"Explain this price movement" (<50 words)
        |
        v
  news_agent    ──"Explain possible reasons" (<75 words)
        |
        v
  summary_agent ──"Combine into a professional email" (<120 words)
        |
        v
  send_email()                  [tools.py — Resend, unchanged]
```

Same three roles as the original, run in the same sequence, each agent's
output threaded into the next agent's prompt exactly as before.

## File map

| File | Role |
|---|---|
| `agent.py` | The three `Agent` (ADK `LlmAgent`) definitions: `price_agent`, `news_agent`, `summary_agent` |
| `tools.py` | `get_stock_info` (Yahoo Finance) and `send_email` (Resend) — reused business logic |
| `runner_utils.py` | `run_agent()` — wraps ADK's session/event ceremony so it can be called like the original SDK's `Runner.run(agent, prompt)` |
| `main.py` | Orchestration script: fetch → price_agent → news_agent → summary_agent → email |
| `requirements.txt` | `google-adk`, `yfinance`, `resend`, `python-dotenv` |

## Key blocks and what changed

### 1. Agent definitions (`agent.py`)

```python
price_agent = Agent(
    name="price_analyst",
    model="gemini-2.5-flash",
    description="Price Analyst",
    instruction="""...""",
)
```

- `instructions=` (OpenAI SDK) → `instruction=` (ADK), singular.
- `name` must be a valid Python identifier in ADK — verified that
  `Agent(name="Price Analyst", ...)` raises a pydantic `ValueError`. Original
  human-readable names (`"Price Analyst"`, `"News Researcher"`,
  `"Investment Summary"`) moved to `description=`; `name=` became
  `price_analyst`, `news_researcher`, `investment_summary`.
- `model="gpt-5.5"` → `model="gemini-2.5-flash"`, since ADK's native model
  integration is Gemini. To keep calling an OpenAI model instead, pass
  `google.adk.models.lite_llm.LiteLlm(model="gpt-5.5")` as `model=`.
- Instructions/word-count constraints (50/75/120 words) are copied verbatim.

### 2. Reused tools (`tools.py`)

`get_stock_info` is untouched — same `yfinance` call, same
current/previous/change math.

`send_email` is the same Resend payload, with one addition:

```python
resend.api_key = os.environ["RESEND_API_KEY"]
```

The original script called `resend.Emails.send(...)` without ever importing
`resend` or setting an API key in that file — it would have raised
`NameError` as written. This isn't a behavior change, just making the
existing logic actually runnable.

### 3. Running an agent turn (`runner_utils.py`)

This is the one piece of real ceremony ADK adds. The OpenAI SDK's Runner is
a stateless one-liner:

```python
result = await Runner.run(agent, prompt)
print(result.final_output)
```

ADK's `Runner` is instance-based and session-oriented — it needs a session
created up front, takes the prompt as a `types.Content` object instead of a
bare string, and streams the run as an async sequence of `Event`s rather
than returning a single result:

```python
async def run_agent(agent, prompt, session_service, user_id):
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id,
    )
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)
    return final_text
```

Because the original called this same pattern three times with only the
agent and prompt varying, that ceremony is factored into this one helper
rather than repeated in `main.py`.

### 4. Orchestration (`main.py`)

Same sequence, same prompts, as the original:

```python
stock = get_stock_info(ticker)
price_result = await run_agent(price_agent, price_prompt, session_service, USER_ID)
news_result = await run_agent(news_agent, news_prompt, session_service, USER_ID)
summary_result = await run_agent(summary_agent, summary_prompt, session_service, USER_ID)
send_email(subject, summary_result)
```

What changed to make it a real script instead of a notebook cell:
- The Colab source used top-level `await` and `!pip install` /
  `getpass()` prompts, which only work interactively. This has a real
  `async def main(ticker)` entry point run via `asyncio.run(...)`.
- Config comes from environment variables (`.env`, loaded via
  `python-dotenv`) and an optional CLI arg for the ticker, instead of
  interactive prompts.
- `_check_env()` fails fast with a clear error if `GOOGLE_API_KEY` or
  `RESEND_API_KEY` is missing, instead of failing deep in a stack trace.

## Setup

1. Install dependencies:
   ```bash
   pip install -r stock_monitor_agent/requirements.txt
   ```
2. Add to the project's `.env` (alongside the existing `GOOGLE_API_KEY`):
   ```
   RESEND_API_KEY=your_resend_key
   ```
3. Set the recipient address in `tools.py` (`send_email`'s `"to"` field) —
   note that a Resend key in sandbox mode can only send to the account's
   own verified address until you verify a sending domain at
   resend.com/domains.

## Running

```bash
python -m stock_monitor_agent.main            # defaults to MSFT
python -m stock_monitor_agent.main MU         # any ticker
```

This prints each agent's output as the pipeline runs, then sends the final
summary as an email alert.

## Verified

- `get_stock_info` pulls real data from Yahoo Finance.
- All three agents run real Gemini calls in sequence, each respecting its
  original word-count constraint.
- A full run against MU (+2.68%) sent successfully via Resend.
- Transient `503 UNAVAILABLE` errors from the Gemini API are a live-service
  hiccup, not a code issue — retry the run.
