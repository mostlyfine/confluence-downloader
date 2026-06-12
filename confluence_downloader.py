#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "markdownify",
# ]
# ///

import argparse
import base64
import csv
import os
import re
import sys
from pathlib import Path

import requests
from markdownify import markdownify as md


def parse_config(filepath: str) -> list[dict]:
    entries = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            page_id = row.get("page_id", "").strip()
            if not page_id or page_id.startswith("#"):
                continue
            output_dir = row.get("output_dir", "").strip()
            if not output_dir:
                continue
            raw_depth = row.get("depth", "").strip() if row.get("depth") else ""
            try:
                depth = int(raw_depth) if raw_depth else 0
            except ValueError:
                depth = 0
            entries.append({"page_id": page_id, "output_dir": output_dir, "depth": depth})
    return entries


def html_to_markdown(html: str) -> str:
    return md(html, heading_style="ATX", bullets="-")


def get_auth_headers(base_url: str, token: str, email: str | None = None) -> dict:
    if "atlassian.net" in base_url:
        if not email:
            raise ValueError("CONFLUENCE_EMAIL is required for Confluence Cloud (atlassian.net)")
        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    return {"Authorization": f"Bearer {token}"}


def sanitize_filename(name: str) -> str:
    result = re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("_")
    return result or "untitled"


def save_markdown(output_dir: str, title: str, page_id: str, content: str) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{sanitize_filename(title)}_{sanitize_filename(page_id)}.md"
    filepath = Path(output_dir) / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def _api_prefix(base_url: str) -> str:
    if "atlassian.net" not in base_url:
        return ""
    return "" if "/wiki" in base_url else "/wiki"


def fetch_page(session: requests.Session, base_url: str, page_id: str) -> dict:
    url = f"{base_url.rstrip('/')}{_api_prefix(base_url)}/rest/api/content/{page_id}"
    response = session.get(url, params={"expand": "body.storage"})
    response.raise_for_status()
    return response.json()


def fetch_children(session: requests.Session, base_url: str, page_id: str) -> list[dict]:
    url = f"{base_url.rstrip('/')}{_api_prefix(base_url)}/rest/api/content/{page_id}/child/page"
    children = []
    start = 0
    limit = 25
    while True:
        response = session.get(url, params={"start": start, "limit": limit})
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        children.extend(results)
        if len(results) < limit:
            break
        start += limit
    return children


def process_page(
    session: requests.Session,
    base_url: str,
    page_id: str,
    output_dir: str,
    depth: int,
    stats: dict,
) -> None:
    try:
        page = fetch_page(session, base_url, page_id)
        title = page["title"]
        html = page["body"]["storage"]["value"]
        markdown = html_to_markdown(html)
        path = save_markdown(output_dir, title, page_id, markdown)
        print(f"[INFO] Saved: {path}")
        stats["saved"] += 1

        if depth > 0:
            children = fetch_children(session, base_url, page_id)
            child_dir = str(Path(output_dir) / f"{sanitize_filename(title)}_{page_id}")
            for child in children:
                process_page(session, base_url, child["id"], child_dir, depth - 1, stats)
    except requests.HTTPError as e:
        print(f"[WARN] Failed to fetch page {page_id}: {e}, skipping", file=sys.stderr)
        stats["skipped"] += 1
    except requests.RequestException as e:
        print(f"[WARN] Network error for page {page_id}: {e}, skipping", file=sys.stderr)
        stats["skipped"] += 1


if __name__ == "__main__":
    pass
