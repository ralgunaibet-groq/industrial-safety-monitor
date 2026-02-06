# Devin + GitHub Issues CLI Automation

A Python CLI tool that integrates the Devin API with GitHub Issues to automatically scope and resolve issues.

## How It Works

1. **Dashboard** - Fetches open issues from the configured GitHub repo and displays them in a formatted CLI table.
2. **Scoping Phase** - Picks the first issue and triggers a Devin session to analyze feasibility, producing a confidence score (0-100).
3. **Execution Phase** - If the confidence score exceeds 80, a second Devin session is launched to implement the fix and open a PR.

## Prerequisites

- Python 3.10+
- A [Devin API key](https://docs.devin.ai/api-reference/overview)
- A GitHub personal access token with `repo` scope

## Setup

### 1. Install dependencies

```bash
pip install rich requests
```

### 2. Export environment variables

```bash
export GITHUB_TOKEN="ghp_your_github_token"
export GITHUB_REPO="owner/repo-name"
export DEVIN_API_KEY="apk_user_your_devin_api_key"
export DEVIN_API_URL="https://api.devin.ai/v1/sessions"  # optional, this is the default
```

### 3. Run the tool

```bash
python main.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with `repo` scope |
| `GITHUB_REPO` | Yes | Target repository in `owner/repo` format |
| `DEVIN_API_KEY` | Yes | Devin API key (`apk_user_*` or `apk_*`) |
| `DEVIN_API_URL` | No | Devin sessions endpoint (defaults to `https://api.devin.ai/v1/sessions`) |

## Configuration

Polling behavior can be adjusted via constants in `main.py`:

- `POLL_INTERVAL_SECONDS` - Seconds between status checks (default: 15)
- `MAX_POLL_ATTEMPTS` - Maximum number of polls before timeout (default: 240, ~60 minutes)
