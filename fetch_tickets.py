#!/usr/bin/env python3
"""
GWS Ticket Dashboard — Jira Fetcher
====================================
Fetches ALL ITH tickets with component = "Google" for the current calendar year.
Paginates fully through the Jira REST API v3 and writes tickets.json,
which is consumed by dashboard.html.

Required env vars:
  JIRA_EMAIL      – e.g. ohmer.sulit@helloconnect.org
  JIRA_TOKEN      – Atlassian API token
  JIRA_BASE_URL   – defaults to https://hellofresh.atlassian.net
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests


# ── helpers ──────────────────────────────────────────────────────────────────

def require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        print(f"ERROR: missing env var {key}", file=sys.stderr)
        sys.exit(1)
    return val


# ── config ───────────────────────────────────────────────────────────────────

JIRA_EMAIL    = require_env("JIRA_EMAIL")
JIRA_TOKEN    = require_env("JIRA_TOKEN")
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://hellofresh.atlassian.net").rstrip("/")

YEAR      = datetime.now().year
START_DATE = f"{YEAR}-01-01"

JQL = (
    f'project = "ITH" AND component = "Google" '
    f'AND created >= "{START_DATE}" '
    f'ORDER BY created DESC'
)

FIELDS = [
    "summary",
    "status",
    "assignee",
    "reporter",
    "created",
    "updated",
    "priority",
    "issuetype",
    "customfield_14636",   # Level  (L0 / L1 / L2 / L3)
    "resolution",
    "components",
]

MAX_PER_PAGE = 100


# ── fetch ─────────────────────────────────────────────────────────────────────

def build_session() -> requests.Session:
    s = requests.Session()
    s.auth = (JIRA_EMAIL, JIRA_TOKEN)
    s.headers.update({"Accept": "application/json"})
    return s


def fetch_page(session: requests.Session, start_at: int) -> dict:
    resp = session.get(
        f"{JIRA_BASE_URL}/rest/api/3/search",
        params={
            "jql":        JQL,
            "startAt":    start_at,
            "maxResults": MAX_PER_PAGE,
            "fields":     ",".join(FIELDS),
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_all(session: requests.Session) -> list:
    issues = []
    start_at = 0

    while True:
        data  = fetch_page(session, start_at)
        batch = data.get("issues", [])
        total = data.get("total", 0)

        issues.extend(batch)
        start_at += len(batch)
        print(f"  {start_at:>5,} / {total:,}", flush=True)

        if start_at >= total or not batch:
            break

    return issues


# ── normalise ─────────────────────────────────────────────────────────────────

def normalise(issue: dict) -> dict:
    f          = issue["fields"]
    level_raw  = f.get("customfield_14636") or {}
    level      = level_raw.get("value")          # "L0" | "L1" | "L2" | "L3" | None

    assignee   = f.get("assignee")  or {}
    reporter   = f.get("reporter")  or {}
    resolution = f.get("resolution") or {}
    priority   = f.get("priority")  or {}
    status     = f.get("status")    or {}
    status_cat = status.get("statusCategory") or {}

    return {
        "key":                 issue["key"],
        "url":                 f"{JIRA_BASE_URL}/browse/{issue['key']}",
        "summary":             f.get("summary") or "",
        "status":              status.get("name") or "Unknown",
        "status_category_key": status_cat.get("key") or "",
        "level":               level,
        "is_automated":        level == "L0",
        "assignee_name":       assignee.get("displayName") or "Unassigned",
        "assignee_email":      assignee.get("emailAddress") or "",
        "reporter_name":       reporter.get("displayName") or "Unknown",
        "created":             f.get("created") or "",
        "updated":             f.get("updated") or "",
        "priority":            priority.get("name") or "Normal",
        "issuetype":           (f.get("issuetype") or {}).get("name") or "",
        "resolution":          resolution.get("name"),
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Fetching GWS (ITH · component:Google) tickets for {YEAR} …")
    session = build_session()
    raw     = fetch_all(session)
    tickets = [normalise(i) for i in raw]

    output = {
        "fetched_at":    datetime.now(timezone.utc).isoformat(),
        "year":          YEAR,
        "jql":           JQL,
        "total_fetched": len(tickets),
        "tickets":       tickets,
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"Done — {len(tickets):,} tickets written to tickets.json")


if __name__ == "__main__":
    main()
