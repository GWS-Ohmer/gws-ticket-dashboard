# gws-ticket-dashboard

Live dashboard for Google Workspace (ITH · component:Google) Jira tickets.  
Auto-refreshes every 15 minutes via GitHub Actions. Hosted on GitHub Pages.

**Live URL:** `https://gws-ohmer.github.io/gws-ticket-dashboard/dashboard.html`

---

## Setup (one-time)

### 1. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name      | Value                                |
|------------------|--------------------------------------|
| `JIRA_EMAIL`     | `ohmer.sulit@helloconnect.org`       |
| `JIRA_TOKEN`     | Your Atlassian API token ([generate here](https://id.atlassian.com/manage-profile/security/api-tokens)) |
| `JIRA_BASE_URL`  | `https://hellofresh.atlassian.net`   |

### 2. Enable GitHub Pages

Go to **Settings → Pages** and set:
- **Source:** `GitHub Actions`

### 3. Trigger the first fetch

Go to **Actions → Refresh Ticket Data → Run workflow**.  
This populates `tickets.json` immediately (instead of waiting for the 15-min cron).

---

## How it works

```
Every 15 min
  GitHub Actions runs fetch_tickets.py
    → Jira REST API v3 (full pagination)
    → JQL: project=ITH AND component=Google AND created>=YYYY-01-01
    → writes tickets.json
    → commits + pushes to main
  GitHub Actions runs pages.yml
    → deploys repo root to GitHub Pages
```

The dashboard reads `tickets.json` on load and auto-reloads every 5 minutes client-side.

---

## Filters

| Filter        | Options |
|---------------|---------|
| Date range    | Custom from / to |
| Status group  | All · ⏳ Ongoing (Group 2) · ✅ Done/Closed (Group 1) |
| Level         | All · 🤖 L0 · L1 · L2 · L3 |
| Search        | Ticket key, summary, assignee |

**Group 1 (Done):** Resolved, Closed, Cancelled, Done  
**Group 2 (Ongoing):** In Progress, Waiting for customer, On Hold, Open, and any other active status

**L0 = Automated** (handled by IT Bot, no human touch)  
**L1/L2/L3 = Manual** (human-handled)
