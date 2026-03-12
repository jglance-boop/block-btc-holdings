#!/usr/bin/env python3
"""Fetch current BTC price from CoinGecko, rankings from BitcoinTreasuries,
and render index.html with live values."""

import json
import os
import re
import shutil
import urllib.request
from datetime import datetime, timezone

TEMPLATE = "index.html"
OUTPUT_DIR = "dist"
TOTAL_BTC = 9001
COST_BASIS = 302_300_000

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd"
)

BTCTREASURIES_URL = "https://bitcointreasuries.net/"

MINERS_AND_DATS = {
    "mara", "riot", "hut 8", "cleanspark", "bitfarms", "cipher mining",
    "core scientific", "bitfufu", "canaan", "dmg blockchain", "hive digital",
    "bitmine", "terawulf", "marathon", "american bitcoin",
    "strategy", "twenty one capital", "metaplanet", "bitcoin standard treasury",
    "strive",
}

FALLBACK_RANK_OVERALL = 14
FALLBACK_RANK_NONMINER = 5


def fetch_btc_price() -> int:
    req = urllib.request.Request(COINGECKO_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return int(data["bitcoin"]["usd"])


def fetch_rankings() -> tuple[int, int]:
    """Try to determine Block's overall and non-miner/non-DAT rank from
    BitcoinTreasuries.net. Falls back to hardcoded values if scraping fails."""
    try:
        req = urllib.request.Request(
            BTCTREASURIES_URL,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        rows = re.findall(
            r'<a[^>]*href="/public-companies/([^"]+)"[^>]*>([^<]+)</a>',
            html,
        )

        overall_rank = FALLBACK_RANK_OVERALL
        nonminer_rank = FALLBACK_RANK_NONMINER
        nm_counter = 0

        for idx, (slug, name) in enumerate(rows, 1):
            name_lower = name.strip().lower()
            slug_lower = slug.lower()

            if "block" in name_lower and ("block, inc" in name_lower or slug_lower == "block"):
                overall_rank = idx
                nonminer_rank = nm_counter + 1
                break

            is_excluded = any(
                e in name_lower or e in slug_lower for e in MINERS_AND_DATS
            )
            if not is_excluded:
                nm_counter += 1

        print(f"Rankings: #{overall_rank} overall, #{nonminer_rank} non-miner/non-DAT")
        return overall_rank, nonminer_rank

    except Exception as e:
        print(f"Could not fetch rankings ({e}), using fallbacks")
        return FALLBACK_RANK_OVERALL, FALLBACK_RANK_NONMINER


def fmt_usd_short(v: float) -> str:
    if abs(v) >= 1e9:
        return f"${v / 1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:,.0f}"


def render(price: int, rank_overall: int, rank_nonminer: int) -> str:
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
        "__RANK_OVERALL__": str(rank_overall),
        "__RANK_NONMINER__": str(rank_nonminer),
    }

    with open(TEMPLATE, "r") as f:
        html = f.read()

    for token, value in replacements.items():
        html = html.replace(token, value)

    return html


def main():
    price = fetch_btc_price()
    print(f"BTC price: ${price:,}")

    rank_overall, rank_nonminer = fetch_rankings()
    html = render(price, rank_overall, rank_nonminer)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
