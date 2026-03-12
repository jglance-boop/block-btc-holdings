#!/usr/bin/env python3
"""Fetch current BTC price from CoinGecko and render index.html with live values."""

import json
import os
import shutil
import urllib.request
from datetime import datetime, timezone

TEMPLATE = "index.html"
OUTPUT_DIR = "dist"
TOTAL_BTC = 9003
COST_BASIS = 302_300_000

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd"
)


def fetch_btc_price() -> int:
    req = urllib.request.Request(COINGECKO_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return int(data["bitcoin"]["usd"])


def fmt_usd_short(v: float) -> str:
    if abs(v) >= 1e9:
        return f"${v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:,.0f}"


def render(price: int) -> str:
    now = datetime.now(timezone.utc)
    month_abbr = now.strftime("%b")
    label = f"{month_abbr}'{now.strftime('%y')}*"
    date_str = now.strftime("%b %d, %Y")

    current_value = TOTAL_BTC * price
    gain = current_value - COST_BASIS
    gain_pct = (gain / COST_BASIS) * 100

    replacements = {
        "__CURRENT_BTC_PRICE__": str(price),
        "__CURRENT_LABEL__": label,
        "__CURRENT_VALUE__": fmt_usd_short(current_value),
        "__CURRENT_PRICE_LABEL__": f"At ${price:,} / BTC ({now.strftime('%b %-d')})",
        "__CURRENT_GAIN_PCT__": f"{'+' if gain >= 0 else ''}{gain_pct:.0f}%",
        "__CURRENT_GAIN_AMT__": f"~{fmt_usd_short(abs(gain))} {'profit' if gain >= 0 else 'loss'}",
        "__LAST_UPDATED__": date_str,
    }

    with open(TEMPLATE, "r") as f:
        html = f.read()

    for token, value in replacements.items():
        html = html.replace(token, value)

    return html


def main():
    price = fetch_btc_price()
    print(f"BTC price: ${price:,}")

    html = render(price)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
