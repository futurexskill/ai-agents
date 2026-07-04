# ADK Agents — Setup Tutorial

A step-by-step guide to setting up Google's Agent Development Kit (ADK), building a simple agent, wiring up an API key, and adding a web search tool. This mirrors the exact steps used to build `hello_agent` in this repo.

## Prerequisites

- Python 3.11+
- A Google account (for generating a Gemini API key)

## 1. Create and activate a virtual environment

```bash
cd adk-agents
python3 -m venv .venv
source .venv/bin/activate
```

You'll know it's active when your shell prompt is prefixed with `(.venv)`.

## 2. Install the ADK

```bash
pip install google-adk
```

This project uses `google-adk==2.3.0`. Verify your install with:

```bash
adk --version
```

## 3. Get a Gemini API key

1. Go to **aistudio.google.com** and sign in.
2. Click **"Get API key"**.
3. Click **"Create API key"** — choose or auto-create a Google Cloud project.
4. Copy the generated key.

This is free to create and comes with a free-tier usage quota — **no billing or payment method is required** to get started.

## 4. Configure environment variables

Create a `.env` file in the project root:

```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_key_here
```

- `GOOGLE_GENAI_USE_VERTEXAI=FALSE` tells ADK to call the Gemini API directly using your API key, instead of routing through a Vertex AI / Google Cloud project (which would need `gcloud` auth and a GCP project instead of an API key).
- Make sure `.env` is listed in `.gitignore` so the key never gets committed:

```
.venv/
.env
__pycache__/
*.pyc
```

## 5. Scaffold the agent

Create a package folder for your agent (e.g. `hello_agent/`) with two files:

**`hello_agent/__init__.py`**
```python
from . import agent
```

**`hello_agent/agent.py`**
```python
from google.adk.agents import Agent

root_agent = Agent(
    name="hello_agent",
    model="gemini-2.5-flash",
    description="A simple hello world agent.",
    instruction="You are a friendly assistant. Greet the user warmly and answer their questions concisely.",
)
```

ADK discovers agents by looking for a `root_agent` variable, so the name matters.

## 6. Run the agent

From the project root (one level above `hello_agent/`):

```bash
adk run hello_agent
```

This starts an interactive terminal chat. Type a message and press Enter; type `exit` to quit.

Alternatively, launch the browser-based dev UI:

```bash
adk web
```

## 7. Add a web search tool

Out of the box, the agent can only answer from the model's training data — it has no access to real-time information (e.g. "who is Argentina playing today?"). ADK ships a built-in Google Search tool you can attach.

Update `hello_agent/agent.py`:

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="hello_agent",
    model="gemini-2.5-flash",
    description="A simple hello world agent.",
    instruction=(
        "You are a friendly assistant. Greet the user warmly and answer "
        "their questions concisely. Use the google_search tool for questions "
        "about current events, real-time data, or anything requiring "
        "up-to-date information."
    ),
    tools=[google_search],
)
```

Two things had to change:
1. Import `google_search` from `google.adk.tools`.
2. Pass it in the `tools=[...]` list on the `Agent`, and mention it in the `instruction` so the model knows when to reach for it.

Re-run `adk run hello_agent` and ask something time-sensitive to confirm it now searches the web before answering.

## Troubleshooting

- **"Aborted!" after a response in `adk run`** — harmless; it just means the input stream closed. It's not an error.
- **Asked for billing/a credit card** — you only hit this if you try to enable paid-tier Vertex AI or Cloud Billing. The Gemini API free tier via `GOOGLE_API_KEY` doesn't require it.
- **Wrong country on a billing account** — Google does not allow changing the country on an existing Cloud Billing account or Payments profile. You must create a new one for the correct country.
