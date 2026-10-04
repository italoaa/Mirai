#!/usr/bin/env python3
"""Fetch the configured RSS/Atom feeds and write the latest items to JSON."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


# Add the feeds you follow here. Both RSS and Atom feeds are supported.
FEEDS = [
    {"name": "Protesilaos Stavrou: Master feed", "url": "https://protesilaos.com/master.xml"},
    {"name": "Xenodium.com", "url": "https://xenodium.com/rss.xml"},
    {"name": "Paul Graham: Essays", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss"},
]

OUTPUT = Path("data/feeds.json")
MAX_ARTICLES_PER_FEED = 5
USER_AGENT = "Mirai RSS reader/1.0 (+https://mirai.ml)"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in element.iter():
        if child is element:
            continue
        if local_name(child.tag) in wanted and child.text:
            return " ".join("".join(child.itertext()).split())
    return ""


def parse_date(value: str) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def clean_description(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = " ".join(value.split())
    return value if len(value) <= 240 else f"{value[:237].rstrip()}..."


def feed_entries(source: dict[str, str]) -> list[dict[str, str]]:
    request = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())

    entries = []
    for element in root.iter():
        if local_name(element.tag) not in {"item", "entry"}:
            continue

        published = parse_date(
            child_text(element, "pubDate", "published", "updated", "date")
        )
        link = child_text(element, "link")
        if not link:
            for child in element.iter():
                if local_name(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib["href"]
                    break
        if not link:
            continue

        entries.append(
            {
                "title": child_text(element, "title") or "Untitled",
                "url": link,
                "source": source["name"],
                "description": clean_description(
                    child_text(element, "description", "summary", "content")
                ),
                "published": published.isoformat() if published else "",
            }
        )
    dated = [entry for entry in entries if entry["published"]]
    undated = [entry for entry in entries if not entry["published"]]
    dated.sort(key=lambda item: item["published"], reverse=True)
    return (dated + undated)[:MAX_ARTICLES_PER_FEED]


def main() -> int:
    now = datetime.now(timezone.utc)
    articles: list[dict[str, str]] = []
    failures = 0

    for source in FEEDS:
        try:
            articles.extend(feed_entries(source))
        except (OSError, ET.ParseError, ValueError) as error:
            failures += 1
            print(f"Warning: could not fetch {source['url']}: {error}", file=sys.stderr)

    if FEEDS and failures == len(FEEDS):
        print("Every configured feed failed; keeping the existing snapshot.", file=sys.stderr)
        return 1

    unique: dict[str, dict[str, str]] = {}
    for article in articles:
        unique.setdefault(article["url"], article)

    output = {
        "updated_at": now.isoformat(),
        "articles": sorted(unique.values(), key=lambda item: item["published"], reverse=True),
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(output['articles'])} articles to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
