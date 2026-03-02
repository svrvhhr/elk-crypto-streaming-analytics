#!/usr/bin/env python3
"""
producer.py — CoinGecko (Demo/Public) -> Kafka

- Polls CoinGecko /coins/markets regularly
- Sends each coin snapshot as a JSON message to a Kafka topic

Requirements:
  pip install requests kafka-python

Usage:
  export KAFKA_BOOTSTRAP_SERVERS="localhost:9093"
  export KAFKA_TOPIC="crypto_market"
  export COINGECKO_DEMO_API_KEY="YOUR_DEMO_KEY"   # optional 
  export VS_CURRENCY="usd"                        # optional
  export PER_PAGE="50"                            # optional
  export POLL_SECONDS="600"                       # optional (1 minute)
  python3 producer.py
"""

import os
import json
import time
import logging
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer


COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"


def env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=[s.strip() for s in bootstrap_servers.split(",") if s.strip()],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",
        retries=5,
        linger_ms=50,
    )


def to_float(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def fetch_markets(demo_api_key: str | None, vs_currency: str, per_page: int, page: int = 1) -> list[dict]:
    headers = {}
    # CoinGecko Demo auth via header: x-cg-demo-api-key
    if demo_api_key:
        headers["x-cg-demo-api-key"] = demo_api_key

    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d",
    }

    r = requests.get(COINGECKO_URL, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected response shape: {type(data)}")
    return data


def normalize_record(raw: dict) -> dict:
    # Add an ingestion timestamp to support time-series queries even if API fields vary
    now = datetime.now(timezone.utc).isoformat()

    # Keep raw fields (useful for later) but also expose consistent keys
    return {
        "ingested_at": now,
        "source": "coingecko",
        "type": "coin_market_snapshot",
        "coin_id": raw.get("id"),
        "symbol": raw.get("symbol"),
        "name": raw.get("name"),

        "current_price": to_float(raw.get("current_price")),
        "market_cap": to_float(raw.get("market_cap")),
        "total_volume": to_float(raw.get("total_volume")),
        "high_24h": to_float(raw.get("high_24h")),
        "low_24h": to_float(raw.get("low_24h")),

        "price_change_percentage_1h_in_currency": to_float(raw.get("price_change_percentage_1h_in_currency")),
        "price_change_percentage_24h_in_currency": to_float(raw.get("price_change_percentage_24h_in_currency")),
        "price_change_percentage_7d_in_currency": to_float(raw.get("price_change_percentage_7d_in_currency")),

        "last_updated": raw.get("last_updated"),
        "raw": raw,
    }



def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9093")
    topic = os.getenv("KAFKA_TOPIC", "cryptodata")
    demo_key = os.getenv("COINGECKO_DEMO_API_KEY")  # optional
    vs_currency = os.getenv("VS_CURRENCY", "usd")
    per_page = env_int("PER_PAGE", 50)
    poll_seconds = env_int("POLL_SECONDS", 600)  # 10 minutes default

    producer = build_producer(kafka_bootstrap)

    logging.info("Starting producer -> topic=%s, bootstrap=%s, poll=%ss, per_page=%s, vs=%s",
                 topic, kafka_bootstrap, poll_seconds, per_page, vs_currency)

    while True:
        try:
            markets = fetch_markets(demo_key, vs_currency, per_page)
            logging.info("Fetched %d records from CoinGecko", len(markets))

            for raw in markets:
                record = normalize_record(raw)
                key = record.get("coin_id") or record.get("symbol") or "unknown"
                producer.send(topic, key=key, value=record)

            producer.flush()
            logging.info("Sent %d messages to Kafka topic=%s", len(markets), topic)

        except requests.HTTPError as e:
            # CoinGecko often uses 429 for rate limiting
            status = getattr(e.response, "status_code", None)
            body = getattr(e.response, "text", "")[:300] if getattr(e, "response", None) else ""
            logging.error("HTTP error (status=%s): %s | %s", status, e, body)
        except Exception as e:
            logging.exception("Unexpected error: %s", e)

        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
