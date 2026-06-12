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
from typing import Optional

import requests
from markdownify import markdownify as md


if __name__ == "__main__":
    pass
