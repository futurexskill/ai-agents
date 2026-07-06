"""Orchestration script, ported from multi_agent_openai.py.

Same sequence as the original: fetch the stock's latest move, run it
through price_agent, feed that into news_agent, feed both into
summary_agent, then email the result. The prompts are unchanged.

What changed to fit ADK/production use:
  - The Colab notebook used top-level `await` and `!pip install` /
    `getpass()` prompts, which only work in an interactive notebook cell.
    This is a standalone script with a real `async def main()` entry
    point, run via `asyncio.run`.
  - Each Runner.run(agent, prompt) call becomes a call to run_agent(),
    which wraps ADK's session + event-stream ceremony (see
    runner_utils.py) but is used the same way: agent in, prompt in,
    final text out.
  - Config (API keys, ticker) comes from environment variables / argv
    instead of interactive prompts.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService

from .agent import news_agent, price_agent, summary_agent
from .runner_utils import run_agent
from .tools import get_stock_info, send_email

load_dotenv()

USER_ID = "stock_monitor_user"

REQUIRED_ENV_VARS = ("GOOGLE_API_KEY", "RESEND_API_KEY")


def _check_env() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them in your .env file."
        )


async def main(ticker: str = "MSFT") -> None:
    _check_env()

    session_service = InMemorySessionService()

    stock = get_stock_info(ticker)

    price_prompt = f"""
Ticker: {stock['ticker']}

Current Price: {stock['current']}

Previous Close: {stock['previous']}

Percentage Change: {stock['change']:.2f}%

Explain this price movement.
"""
    price_result = await run_agent(price_agent, price_prompt, session_service, USER_ID)
    print(price_result)

    news_prompt = f"""
The stock {stock['ticker']} moved {stock['change']:.2f}% today.

Use your knowledge and reasoning to explain possible reasons
behind this movement.
"""
    news_result = await run_agent(news_agent, news_prompt, session_service, USER_ID)
    print(news_result)

    summary_prompt = f"""
Price Analysis

----------------

{price_result}

News Analysis

----------------

{news_result}

Create a professional investment summary suitable for an email.
"""
    summary_result = await run_agent(summary_agent, summary_prompt, session_service, USER_ID)
    print(summary_result)

    subject = f"🚨 {stock['ticker']} Alert ({stock['change']:.2f}%)"
    response = send_email(subject, summary_result)
    print(response)


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    asyncio.run(main(ticker_arg))
