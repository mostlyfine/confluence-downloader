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
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            if row[0].strip().lower() == "page_id":
                continue
            if len(row) < 2:
                continue
            page_id = row[0].strip()
            output_dir = row[1].strip()
            depth = int(row[2].strip()) if len(row) > 2 and row[2].strip() else 0
            entries.append({"page_id": page_id, "output_dir": output_dir, "depth": depth})
    return entries


if __name__ == "__main__":
    pass
