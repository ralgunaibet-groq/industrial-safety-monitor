#!/usr/bin/env python3
"""CLI automation tool integrating Devin API with GitHub Issues."""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv(Path(__file__).resolve().parent / ".env")

console = Console()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
DEVIN_API_URL = os.environ.get("DEVIN_API_URL", "https://api.devin.ai/v1/sessions")
DEVIN_API_KEY = os.environ.get("DEVIN_API_KEY", "")

POLL_INTERVAL_SECONDS = 15
MAX_POLL_ATTEMPTS = 240


def validate_env() -> None:
    missing = []
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not GITHUB_REPO:
        missing.append("GITHUB_REPO")
    if not DEVIN_API_KEY:
        missing.append("DEVIN_API_KEY")
    if missing:
        console.print(
            f"[bold red]Missing environment variables: {', '.join(missing)}[/bold red]"
        )
        sys.exit(1)


def fetch_open_issues() -> list[dict]:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    params = {"state": "open", "per_page": 25, "sort": "created", "direction": "asc"}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    issues = [i for i in resp.json() if "pull_request" not in i]
    return issues


def display_dashboard(issues: list[dict]) -> None:
    table = Table(title="Open GitHub Issues", show_lines=True)
    table.add_column("#", style="bold cyan", width=6)
    table.add_column("Title", style="bold white", min_width=30)
    table.add_column("Labels", style="yellow")
    table.add_column("Created", style="green")
    table.add_column("Author", style="magenta")

    for issue in issues:
        labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))
        table.add_row(
            str(issue["number"]),
            issue["title"],
            labels or "-",
            issue["created_at"][:10],
            issue["user"]["login"],
        )

    console.print(table)


def create_devin_session(prompt: str, title: str | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {DEVIN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict = {"prompt": prompt}
    if title:
        payload["title"] = title
    resp = requests.post(DEVIN_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_session_details(session_id: str) -> dict:
    url = f"{DEVIN_API_URL}/{session_id}"
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_session_message(session_id: str, message: str) -> dict:
    url = f"{DEVIN_API_URL}/{session_id}/message"
    headers = {
        "Authorization": f"Bearer {DEVIN_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json={"message": message}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def poll_session_until_done(session_id: str, label: str) -> dict:
    console.print(f"\n[bold blue]Polling {label} session: {session_id}[/bold blue]")
    blocked_nudges = 0
    max_blocked_nudges = 3
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        details = get_session_details(session_id)
        status = details.get("status_enum", details.get("status", "unknown"))
        console.print(
            f"  [{attempt}/{MAX_POLL_ATTEMPTS}] Status: [yellow]{status}[/yellow]"
        )
        if status in ("finished", "stopped"):
            return details
        if status in ("expired", "error"):
            console.print(f"[bold red]Session ended with status: {status}[/bold red]")
            return details
        if status == "blocked" and blocked_nudges < max_blocked_nudges:
            blocked_nudges += 1
            console.print(
                f"  [yellow]Session is blocked. Sending nudge ({blocked_nudges}/{max_blocked_nudges})...[/yellow]"
            )
            nudge = (
                "Please continue and complete the task. "
                "Output your final result as JSON: "
                '{"confidence_score": <0-100>, "reasoning": "<text>"}\n'
                "Then stop working."
            )
            try:
                send_session_message(session_id, nudge)
            except requests.RequestException as exc:
                console.print(f"  [dim]Nudge failed: {exc}[/dim]")
        time.sleep(POLL_INTERVAL_SECONDS)
    console.print("[bold red]Polling timed out.[/bold red]")
    return get_session_details(session_id)


def extract_json_from_text(text: str) -> dict | None:
    structured_patterns = [
        r'\{\s*"confidence_score"\s*:\s*\d+.*?"reasoning"\s*:\s*"[^"]*"\s*\}',
        r"\{[^{}]*confidence_score[^{}]*reasoning[^{}]*\}",
    ]
    for pattern in structured_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if "confidence_score" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict) and "confidence_score" in parsed:
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    return None


def parse_scoping_result(session_details: dict) -> dict | None:
    structured = session_details.get("structured_output")
    if structured:
        if isinstance(structured, dict) and "confidence_score" in structured:
            return structured
        if isinstance(structured, str):
            result = extract_json_from_text(structured)
            if result:
                return result

    messages = session_details.get("messages", [])
    for msg in reversed(messages):
        text = msg.get("message", msg.get("content", ""))
        if not text:
            continue
        result = extract_json_from_text(text)
        if result:
            return result

    return None


def run_scoping_phase(issue: dict) -> dict | None:
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_body = issue.get("body", "") or "(no description)"
    issue_labels = ", ".join(lbl["name"] for lbl in issue.get("labels", []))

    console.print(
        Panel(
            f"[bold]Issue #{issue_number}:[/bold] {issue_title}",
            title="Scoping Phase",
            border_style="cyan",
        )
    )

    prompt = (
        f"You are scoping a GitHub issue for the repository {GITHUB_REPO}.\n\n"
        f"Issue #{issue_number}: {issue_title}\n"
        f"Labels: {issue_labels}\n\n"
        f"Issue Body:\n{issue_body}\n\n"
        "Analyze this issue and determine the feasibility and complexity of implementing it. "
        "Consider the scope of changes needed, potential risks, and whether the requirements are clear enough.\n\n"
        "IMPORTANT: You MUST conclude your analysis by outputting EXACTLY this JSON format as your final output:\n"
        '{"confidence_score": <0-100>, "reasoning": "<brief explanation of your assessment>"}\n\n'
        "The confidence_score should reflect how confident you are that this issue can be successfully resolved:\n"
        "- 90-100: Simple, well-defined task with clear requirements\n"
        "- 70-89: Moderate complexity, requirements mostly clear\n"
        "- 50-69: Complex task or ambiguous requirements\n"
        "- Below 50: Very complex, unclear, or risky\n\n"
        "Also update the structured output with this same JSON object.\n"
        "After outputting the JSON, stop working."
    )

    session = create_devin_session(
        prompt=prompt,
        title=f"Scope: Issue #{issue_number} - {issue_title}",
    )
    session_id = session["session_id"]
    session_url = session.get("url", "")
    console.print(f"[green]Scoping session created:[/green] {session_url}")

    details = poll_session_until_done(session_id, "scoping")
    result = parse_scoping_result(details)

    if result:
        score = result.get("confidence_score", 0)
        reasoning = result.get("reasoning", "N/A")
        color = "green" if score > 80 else "yellow" if score > 50 else "red"
        console.print(
            Panel(
                f"[bold]Confidence Score:[/bold] [{color}]{score}[/{color}]\n"
                f"[bold]Reasoning:[/bold] {reasoning}",
                title="Scoping Result",
                border_style=color,
            )
        )
        return result

    console.print(
        "[bold red]Could not parse confidence score from scoping session.[/bold red]"
    )
    console.print("[dim]Dumping last 3 messages for debugging:[/dim]")
    for msg in (details.get("messages") or [])[-3:]:
        text = msg.get("message", msg.get("content", ""))[:500]
        console.print(f"  [dim]{text}[/dim]")
    return None


def run_execution_phase(issue: dict, scoping_result: dict) -> None:
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_body = issue.get("body", "") or "(no description)"
    reasoning = scoping_result.get("reasoning", "")

    console.print(
        Panel(
            f"[bold]Launching execution for Issue #{issue_number}[/bold]",
            title="Execution Phase",
            border_style="green",
        )
    )

    prompt = (
        f"You are tasked with implementing a fix/feature for the repository {GITHUB_REPO}.\n\n"
        f"Issue #{issue_number}: {issue_title}\n\n"
        f"Issue Body:\n{issue_body}\n\n"
        f"Scoping Analysis:\n{reasoning}\n\n"
        "Instructions:\n"
        "1. Clone the repository and understand the codebase.\n"
        "2. Implement the necessary changes to resolve this issue.\n"
        "3. Write clean, well-tested code following the project's conventions.\n"
        "4. Create a pull request with a clear description of your changes.\n"
        f"5. The PR should reference Issue #{issue_number}.\n"
    )

    session = create_devin_session(
        prompt=prompt,
        title=f"Fix: Issue #{issue_number} - {issue_title}",
    )
    session_id = session["session_id"]
    session_url = session.get("url", "")
    console.print(f"[green]Execution session created:[/green] {session_url}")

    details = poll_session_until_done(session_id, "execution")
    status = details.get("status_enum", details.get("status", "unknown"))

    pr_info = details.get("pull_request")
    if pr_info and pr_info.get("url"):
        console.print(
            Panel(
                f"[bold green]PR Created:[/bold green] {pr_info['url']}",
                title="Result",
                border_style="green",
            )
        )
    else:
        console.print(
            f"[yellow]Execution session finished with status: {status}. "
            f"Check the session for details: {session_url}[/yellow]"
        )


def main() -> None:
    console.print(
        Panel(
            "[bold]Devin + GitHub Issues Automation[/bold]",
            border_style="bright_blue",
        )
    )

    validate_env()

    console.print(
        f"\n[bold]Fetching open issues from [cyan]{GITHUB_REPO}[/cyan]...[/bold]\n"
    )
    issues = fetch_open_issues()

    if not issues:
        console.print("[yellow]No open issues found.[/yellow]")
        sys.exit(0)

    display_dashboard(issues)

    target_issue = issues[0]
    console.print(
        f"\n[bold]Auto-selecting first issue:[/bold] "
        f"#{target_issue['number']} - {target_issue['title']}\n"
    )

    scoping_result = run_scoping_phase(target_issue)
    if scoping_result is None:
        console.print("[bold red]Scoping failed. Aborting.[/bold red]")
        sys.exit(1)

    score = scoping_result.get("confidence_score", 0)
    if score > 80:
        console.print(
            f"\n[bold green]Confidence score {score} > 80. "
            f"Proceeding to execution phase.[/bold green]\n"
        )
        run_execution_phase(target_issue, scoping_result)
    else:
        console.print(
            f"\n[bold yellow]Confidence score {score} <= 80. "
            f"Skipping execution phase. Manual review recommended.[/bold yellow]\n"
        )

    console.print("\n[bold bright_blue]Done.[/bold bright_blue]")


if __name__ == "__main__":
    main()
