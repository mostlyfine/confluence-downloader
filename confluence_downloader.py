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


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("_")


if __name__ == "__main__":
    pass
