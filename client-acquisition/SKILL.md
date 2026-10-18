---
name: client-acquisition
description: Automatically find and contact new clients for a website / web design business. Use when someone wants to get more customers for their web agency, find local businesses without a website or with outdated websites, audit websites to generate sales leads, or send personalized cold outreach emails with follow-ups.
license: MIT
compatibility: Requires Python 3.9+ and internet access. Uses a Google Places API key and SMTP credentials for sending email.
metadata: {"openclaw": {"requires": {"env": ["GOOGLE_PLACES_API_KEY"]}, "primaryEnv": "GOOGLE_PLACES_API_KEY"}}
---

# Client Acquisition for Website Businesses

An automated pipeline that turns Google Maps listings into booked meetings for a website/web design business:

```
find (Google Places) -> audit (website check + score) -> email outreach -> follow-up
```

Everything is done by one dependency-free script, [`scripts/acquire.py`](scripts/acquire.py). State is kept in `leads.csv`, which can be opened in Excel or Google Sheets.

## Setup

```bash
cp references/acquisition.example.json acquisition.json   # edit offer, sender, queries, cities

export GOOGLE_PLACES_API_KEY="..."   # Google Cloud -> enable "Places API (New)"
export SMTP_HOST="smtp.example.com" SMTP_PORT=465 SMTP_USER="..." SMTP_PASSWORD="..."
export SENDER_EMAIL="max@muster-webdesign.de"
```

Use a separate sending domain or mailbox (e.g. `hallo@get-musterweb.de`) with SPF, DKIM and DMARC set up so the main domain's reputation is protected.

## Commands

```bash
python scripts/acquire.py find --query "Friseur" --city "München"   # add leads
python scripts/acquire.py audit                                     # check websites, find emails, score
python scripts/acquire.py report                                    # pipeline overview + top leads
python scripts/acquire.py outreach                                  # write .eml drafts to drafts/
python scripts/acquire.py outreach --send --limit 20                # send highest-scoring leads
python scripts/acquire.py followup --send --days 5                  # one follow-up after 5 days
python scripts/acquire.py run --send                                # find+audit+outreach+followup (cron)
```

Without `--send` nothing leaves the machine; review drafts first.

## How leads are scored

The audit fetches the homepage (and Impressum/Kontakt pages to find an email address) and records:

| Issue | Weight | Detected by |
|-------|--------|-------------|
| `no_website` | 50 | No website on the Google listing |
| `unreachable` | 40 | Website does not load |
| `not_mobile` | 25 | No `viewport` meta tag |
| `no_https` | 20 | Final URL is not HTTPS |
| `outdated` | 15 | Copyright year 3+ years old |
| `low_pagespeed` | 15 | Google PageSpeed mobile score < 50 (skip with `--no-pagespeed`) |
| `slow` | 10 | Homepage takes > 3 s |
| `no_title` | 5 | Missing/short `<title>` |

Plus up to 20 points for many Google reviews (established businesses that can pay) and 5 for having a contact. Only leads at or above `min_score` (default 20) are contacted. The top three issues are written into the email as concrete, personalized observations.

## Lead statuses

`new` -> `contacted` -> set manually in `leads.csv` to `replied`, `won`, `not_interested` or `do_not_contact`. Leads in any of those final statuses are never contacted again. Each lead gets at most one initial email and one follow-up; `--limit` caps emails per day across both.

## Customizing

- **Design (HTML emails):** emails are sent as a styled HTML version with a plain-text fallback. Match your own website with the `brand` block in `acquisition.json`: `color` (button and links), `header_color`, `background`, `font` and `logo_url` (a publicly reachable PNG, ideally white on the header color; without it the company name is shown). The layouts are `references/templates/initial_email.html` and `followup_email.html` (point `templates.initial_email_html` / `templates.followup_email_html` at your own files). They also accept `{issue_items}` (the issues as `<li>` items), `{logo}`, `{color}`, `{header_color}`, `{background}` and `{font}`. Set `"html": false` to send plain text only.
- **Email text:** edit `references/templates/initial_email.txt` and `followup_email.txt`, or point `templates.initial_email` / `templates.followup_email` in `acquisition.json` at your own files. First line is the subject, then `---`, then the body. Placeholders: `{name}`, `{issue_bullets}`, `{reputation_line}`, `{offer}`, `{booking_link}`, `{sender_name}`, `{sender_company}`, `{sender_phone}`, `{sender_website}`, plus any `leads.csv` column.
- **Target niches:** businesses that depend on local search convert best (Handwerker, Friseure, Physiotherapie, Restaurants, Ärzte, Kosmetik).

## Running it automatically

See [references/automation.md](references/automation.md) for a cron job and a GitHub Actions workflow that run the pipeline every weekday morning.
