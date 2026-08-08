#!/usr/bin/env python3
"""Coleta RSS, elimina duplicatas e gera o boletim consumido pelo GPT."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
OUTPUT = ROOT / "docs" / "latest.json"
USER_AGENT = "RadarPoliticoMundial/1.0 (+GitHub Actions; RSS reader)"

POLITICAL_TERMS = {
    "politica", "politics", "political", "government", "governo", "congresso",
    "congress", "senado", "senate", "eleicao", "election", "presidente",
    "president", "ministro", "minister", "parlamento", "parliament", "diplomacia",
    "diplomacy", "guerra", "war", "sanctions", "sancoes", "suprema", "supreme",
    "democracia", "democracy", "policy", "partido", "party", "geopolitica"
}
STOP = {"para", "com", "uma", "das", "dos", "que", "por", "the", "and", "for",
        "from", "this", "sobre", "como", "mais", "de", "do", "da", "em", "a", "o"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    return {w for w in normalize(text).split() if len(w) > 2 and w not in STOP}


def parse_date(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def fetch(feed: dict, limit: int) -> list[dict]:
    request = urllib.request.Request(feed["url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    rows = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        source_node = item.find("source")
        source = (source_node.text or feed["name"]).strip() if source_node is not None else feed["name"]
        published = parse_date(item.findtext("pubDate"))
        rows.append({
            "id": hashlib.sha256((title + link).encode()).hexdigest()[:16],
            "title": title,
            "url": link,
            "source": source,
            "feed": feed["name"],
            "priority": float(feed.get("priority", 1)),
            "published_at": published.isoformat(),
            "_published": published,
            "_tokens": tokens(title),
        })
    return rows


def similarity(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def rank(rows: list[dict], now: datetime) -> list[dict]:
    # Títulos idênticos ou quase idênticos publicados em vários feeds formam um assunto.
    groups: list[list[dict]] = []
    for row in sorted(rows, key=lambda r: r["_published"], reverse=True):
        group = next((g for g in groups if similarity(row["_tokens"], g[0]["_tokens"]) >= .46), None)
        if group is None:
            groups.append([row])
        else:
            group.append(row)

    ranked = []
    for group in groups:
        best = max(group, key=lambda r: r["priority"])
        age_hours = max(0, (now - best["_published"]).total_seconds() / 3600)
        recency = math.exp(-age_hours / 36)
        political_hits = len(best["_tokens"] & POLITICAL_TERMS)
        source_count = len({r["source"] for r in group})
        score = 45 * recency + 18 * math.log1p(source_count) + 8 * min(political_hits, 3) + 10 * best["priority"]
        ranked.append({
            "id": best["id"], "title": best["title"], "url": best["url"],
            "source": best["source"], "published_at": best["published_at"],
            "score": round(score, 2), "corroborating_sources": sorted({r["source"] for r in group}),
            "signals": {"source_count": source_count, "social_metrics_available": False}
        })
    return sorted(ranked, key=lambda r: r["score"], reverse=True)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    rows, errors = [], []
    for feed in config["feeds"]:
        try:
            rows.extend(fetch(feed, config["max_items_per_feed"]))
        except Exception as exc:  # uma fonte com falha não derruba o boletim
            errors.append({"feed": feed["name"], "error": type(exc).__name__})
    ranked = rank(rows, now)[: config["output_items"]]
    payload = {
        "generated_at": now.isoformat(),
        "next_update_expected_at": (now + timedelta(hours=4)).isoformat(),
        "scope": "Política nacional e internacional",
        "methodology": "RSS + recência + relevância política + repetição entre fontes",
        "warning": "Não representa ranking oficial de acessos ou comentários de X/Instagram.",
        "items": ranked,
        "source_status": {"configured": len(config["feeds"]), "successful": len(config["feeds"]) - len(errors), "errors": errors}
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gerados {len(ranked)} itens; {len(errors)} fonte(s) com erro.")


if __name__ == "__main__":
    main()
