"""Business logic reused as-is from multi_agent_openai.py.

get_stock_info's math and send_email's payload are unchanged. The only
addition is explicitly setting resend.api_key, since the original script
called resend.Emails.send without ever importing resend or configuring it
in this file.
"""

import os

import resend
import yfinance as yf


def get_stock_info(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.history(period="2d")

    current = info["Close"].iloc[-1]
    previous = info["Close"].iloc[-2]
    change = (current - previous) / previous * 100

    return {
        "ticker": ticker,
        "current": current,
        "previous": previous,
        "change": change,
    }


def send_email(subject: str, body: str):
    resend.api_key = os.environ["RESEND_API_KEY"]

    response = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "futurexskill@gmail.com",
        "subject": subject,
        "html": f"""
        <html>
        <body style="font-family:Arial">
        <h2>📈 AI Stock Alert</h2>
        <hr>
        <p>{body}</p>
        </body>
        </html>
        """,
    })

    return response
