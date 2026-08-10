# Job Search Agent

Checks Greenhouse, Lever, RemoteOK, and We Work Remotely daily for listings
that match `resume_profile.json`, and emails you only the new matches.

## What it does each run

1. Pulls current openings from a curated list of company boards
   (`companies.json`) plus RemoteOK and We Work Remotely.
2. Scores each listing against `resume_profile.json` (title match, keyword
   overlap, location/remote preference).
3. Drops anything below the score threshold or hitting an exclude keyword.
4. Emails you the new matches (skips ones already sent) and updates
   `data/seen.json` so you don't get repeat notifications.

## Setup (10 minutes)

### 1. Push this to a GitHub repo
Create a new **private** repo and push this folder to it.

### 2. Create a Gmail App Password (or use another SMTP provider)
Regular Gmail passwords won't work with smtplib. Create an App Password:
Google Account → Security → 2-Step Verification → App passwords.
(Any SMTP provider works — SendGrid, Outlook, etc. — just adjust
`SMTP_HOST`/`SMTP_PORT` in the workflow env if not using Gmail.)

### 3. Add repo secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `SMTP_USER` | your Gmail address |
| `SMTP_PASS` | the 16-character App Password |
| `NOTIFY_EMAIL` | where you want digests sent (can be same as SMTP_USER) |

### 4. That's it
The workflow (`.github/workflows/job-search.yml`) runs automatically every
day at 12:00 UTC (7am Central). You can also trigger it manually anytime:
repo → **Actions** tab → "Job Search Agent" → **Run workflow**.

## Tuning it to your search

- **`resume_profile.json`** — edit `target_titles` and `core_keywords` as
  your search evolves. `min_score_to_notify` controls how strict matching
  is (lower = more results, more noise).
- **`companies.json`** — this is a *starter list* of SaaS/tech companies
  known to use Greenhouse/Lever. Add companies you're actually interested
  in — find their board slug by checking their careers page URL
  (e.g. `boards.greenhouse.io/COMPANYSLUG` or `jobs.lever.co/COMPANYSLUG`).
  Not every company on the list will have open Implementation/CS/PM roles
  at any given time — that's expected, the scorer just filters them out.
- **`main.py` → `WWR_CATEGORIES`** — We Work Remotely has other category
  RSS feeds (e.g. `remote-management-and-finance-jobs`) you can add.

## Running it locally to test

```bash
cd job-agent
python3 main.py
```

Without `SMTP_USER` set, it prints matches to the console instead of
emailing — good for a first dry run before wiring up email.

## Known limitations

- LinkedIn and Indeed don't have public search APIs and block scraping, so
  they're intentionally not included. If you want broader "general search"
  coverage across many employers at once (not just the curated list), the
  next step would be adding the Adzuna API (free tier, real keyword+location
  search) — happy to wire that in if useful.
- Job matching is keyword/title based, not semantic — it'll occasionally
  miss a good-fit role that's phrased unusually, or include a mediocre one
  that happens to share keywords. Adjust `min_score_to_notify` if it feels
  too loose or too strict.
