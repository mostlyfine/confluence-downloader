# Confluence Downloader

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![uv](https://img.shields.io/badge/uv-managed-purple.svg)

A CLI tool that downloads Confluence pages and converts them to Markdown files. Supports both Confluence Cloud and Confluence Server/Data Center, with recursive page hierarchy traversal.

## Features

- Downloads Confluence pages as Markdown files
- Converts HTML content to Markdown (ATX headings, clean formatting)
- Recursively traverses child page hierarchies with configurable depth
- Supports Confluence Cloud (Basic Auth) and Server/Data Center (Bearer token)
- Configurable request throttling to avoid rate limiting
- Skips pages with empty content while still recursing into children

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended — handles dependencies automatically via PEP 723 inline metadata)

## Setup

Copy `.env.sample` to `.env` and fill in your credentials:

```bash
cp .env.sample .env
```

| Variable | Required | Description |
|---|---|---|
| `CONFLUENCE_URL` | Yes | Base URL of your Confluence instance (e.g. `https://your-domain.atlassian.net`) |
| `CONFLUENCE_API_TOKEN` | Yes | API Token (Cloud) or Personal Access Token (Server/DC) |
| `CONFLUENCE_EMAIL` | Cloud only | Email address associated with the API Token |

Load the variables before running:

```bash
source .env   # or: export $(grep -v '^#' .env | xargs)
```

## Configuration

Create a CSV config file (see `config.csv.sample`):

```csv
page_id,output_dir,depth
3200335760,downloads/PRD,2
3855900161,downloads,0
```

| Column | Required | Description |
|---|---|---|
| `page_id` | Yes | Confluence page ID |
| `output_dir` | Yes | Directory where downloaded files are saved |
| `depth` | No | How many levels of child pages to recurse (default: `0`) |

Lines whose `page_id` starts with `#` are treated as comments and skipped.

**File naming:** Each page is saved as `{title}_{page_id}.md`. Child pages are placed in a subdirectory named after the parent page title.

## Usage

```bash
uv run confluence_downloader.py <config.csv> [--wait SECONDS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--wait SECONDS` | `1.0` | Seconds to wait between page downloads |

**Examples:**

```bash
# Download with default 1-second wait between requests
uv run confluence_downloader.py config.csv

# Increase wait time for stricter rate-limited instances
uv run confluence_downloader.py config.csv --wait 3
```

## Development

Run the test suite:

```bash
uv run --with pytest --with requests --with markdownify pytest tests/
```

## License

MIT License

Copyright (c) 2026 mostlyfine

