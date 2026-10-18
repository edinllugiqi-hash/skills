#!/usr/bin/env python3
"""Automated client acquisition for a website-building business.

Pipeline:  find -> audit -> outreach (email) / call (ElevenLabs agent) -> followup

    python acquire.py find --query "Friseur" --city "München"
    python acquire.py audit
    python acquire.py outreach            # writes drafts only
    python acquire.py outreach --send     # sends via SMTP
    python acquire.py followup --send
    python acquire.py call                # ElevenLabs outbound call for leads without email
    python acquire.py run --send          # everything above from acquisition.json (for cron)

All state lives in leads.csv, which can be opened and edited in Excel/Sheets.
Set `status` to replied / won / not_interested / do_not_contact to stop further contact.
Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

FIELDS = [
    "id", "name", "address", "phone", "website", "rating", "reviews", "query",
    "audited", "has_website", "https", "mobile_friendly", "load_seconds",
    "pagespeed", "copyright_year", "email", "issues", "score",
    "status", "contacted_at", "followup_at", "called_at", "notes",
]
STOP_STATUSES = {"replied", "won", "not_interested", "do_not_contact", "bounced"}
USER_AGENT = "Mozilla/5.0 (compatible; WebsiteAudit/1.0)"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IGNORED_EMAIL_PARTS = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", ".webp", ".svg", "domain.")

ISSUE_TEXT = {
    "no_website": "Sie haben aktuell keine eigene Website. Viele Kunden suchen zuerst bei Google und landen dann bei der Konkurrenz.",
    "unreachable": "Ihre Website war bei unserem Test nicht erreichbar.",
    "no_https": "Ihre Website ist nicht verschlüsselt (kein HTTPS). Browser zeigen Besuchern deshalb „Nicht sicher“ an.",
    "not_mobile": "Ihre Website ist nicht für Smartphones optimiert, obwohl die meisten Besucher mobil kommen.",
    "slow": "Ihre Startseite lädt langsam ({load_seconds} Sekunden). Viele Besucher springen schon nach 3 Sekunden ab.",
    "low_pagespeed": "Google bewertet die mobile Ladegeschwindigkeit Ihrer Website mit nur {pagespeed}/100 Punkten.",
    "outdated": "Ihre Website wirkt veraltet (letzter Copyright-Vermerk: {copyright_year}).",
    "no_title": "Ihrer Startseite fehlt ein aussagekräftiger Seitentitel, das schadet dem Google-Ranking.",
}
ISSUE_WEIGHT = {
    "no_website": 50, "unreachable": 40, "not_mobile": 25, "no_https": 20,
    "outdated": 15, "low_pagespeed": 15, "slow": 10, "no_title": 5,
}


# --------------------------------------------------------------------------- storage

def load_leads(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {row["id"]: {k: row.get(k, "") for k in FIELDS} for row in csv.DictReader(f)}


def save_leads(path: Path, leads: dict[str, dict]) -> None:
    tmp = path.with_suffix(".tmp")
    rows = sorted(leads.values(), key=lambda r: -int(r["score"] or 0))
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def load_config(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------- http

def http_get(url: str, timeout: float = 15) -> tuple[str, str, float]:
    """Returns (final_url, body, seconds)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "de,en"})
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(2_000_000).decode(resp.headers.get_content_charset() or "utf-8", "replace")
        return resp.geturl(), body, time.monotonic() - start


def http_json(url: str, payload: dict | None = None, headers: dict | None = None, timeout: float = 60) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} from {url.split('?')[0]}: {e.read()[:500].decode('utf-8', 'replace')}") from e


# --------------------------------------------------------------------------- find

def find_places(query: str, api_key: str, max_results: int) -> list[dict]:
    """Google Places API (New) Text Search."""
    fields = ",".join([
        "places.id", "places.displayName", "places.formattedAddress", "places.websiteUri",
        "places.internationalPhoneNumber", "places.rating", "places.userRatingCount",
        "places.businessStatus", "nextPageToken",
    ])
    results: list[dict] = []
    token = None
    while len(results) < max_results:
        body = {"textQuery": query, "languageCode": "de", "pageSize": 20}
        if token:
            body["pageToken"] = token
        data = http_json(
            "https://places.googleapis.com/v1/places:searchText", body,
            {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": fields},
        )
        results.extend(data.get("places", []))
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(2)
    return results[:max_results]


def cmd_find(args, cfg, leads) -> int:
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        sys.exit("GOOGLE_PLACES_API_KEY is not set (Google Cloud Console -> Places API (New)).")
    searches = [(args.query, args.city)] if args.query else [
        (q, c) for q in cfg.get("queries", []) for c in cfg.get("cities", [])
    ]
    if not searches:
        sys.exit("Pass --query/--city or define queries and cities in acquisition.json.")
    added = 0
    for query, city in searches:
        text = f"{query} in {city}" if city else query
        for p in find_places(text, api_key, args.max):
            if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL" or p["id"] in leads:
                continue
            leads[p["id"]] = {k: "" for k in FIELDS} | {
                "id": p["id"],
                "name": p.get("displayName", {}).get("text", ""),
                "address": p.get("formattedAddress", ""),
                "phone": p.get("internationalPhoneNumber", "").replace(" ", ""),
                "website": p.get("websiteUri", ""),
                "rating": p.get("rating", ""),
                "reviews": p.get("userRatingCount", ""),
                "query": text,
                "status": "new",
            }
            added += 1
        print(f"{text}: {added} new leads so far")
    print(f"Added {added} leads ({len(leads)} total).")
    return added


# --------------------------------------------------------------------------- audit

def extract_emails(html: str, site_host: str) -> list[str]:
    found = []
    for m in EMAIL_RE.findall(urllib.parse.unquote(html)):
        e = m.lower().rstrip(".")
        if any(bad in e for bad in IGNORED_EMAIL_PARTS) or e in found:
            continue
        found.append(e)
    # Prefer addresses on the business's own domain.
    host = site_host.removeprefix("www.")
    return sorted(found, key=lambda e: (not e.endswith("@" + host), e))


def contact_links(html: str, base: str) -> list[str]:
    links = []
    for href in re.findall(r"""href=["']([^"'#]+)["']""", html, re.I):
        if re.search(r"impressum|kontakt|contact|imprint", href, re.I):
            url = urllib.parse.urljoin(base, href)
            if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(base).netloc and url not in links:
                links.append(url)
    return links[:3]


def pagespeed_score(url: str, api_key: str | None) -> str:
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if api_key:
        params["key"] = api_key
    try:
        data = http_json("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(params), timeout=90)
        return str(round(data["lighthouseResult"]["categories"]["performance"]["score"] * 100))
    except Exception as e:  # PageSpeed is optional; never fail the audit on it
        print(f"  pagespeed skipped: {e}")
        return ""


def audit_lead(lead: dict, pagespeed_key: str | None, use_pagespeed: bool) -> None:
    issues: list[str] = []
    website = lead["website"].strip()
    lead["has_website"] = "yes" if website else "no"
    if not website:
        issues.append("no_website")
    else:
        if not re.match(r"https?://", website):
            website = "http://" + website
        try:
            final_url, html, seconds = http_get(website)
        except Exception:
            issues.append("unreachable")
        else:
            lead["load_seconds"] = f"{seconds:.1f}"
            lead["https"] = "yes" if final_url.startswith("https://") else "no"
            lead["mobile_friendly"] = "yes" if re.search(r"<meta[^>]+name=[\"']viewport", html, re.I) else "no"
            years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?((?:19|20)\d{2})", html, re.I)]
            lead["copyright_year"] = str(max(years)) if years else ""
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)

            if lead["https"] == "no":
                issues.append("no_https")
            if lead["mobile_friendly"] == "no":
                issues.append("not_mobile")
            if seconds > 3:
                issues.append("slow")
            if years and max(years) <= datetime.now().year - 3:
                issues.append("outdated")
            if not title or len(title.group(1).strip()) < 5:
                issues.append("no_title")

            host = urllib.parse.urlparse(final_url).netloc
            emails = extract_emails(html, host)
            if not emails:
                for link in contact_links(html, final_url):
                    try:
                        emails = extract_emails(http_get(link)[1], host)
                    except Exception:
                        continue
                    if emails:
                        break
            if emails and not lead["email"]:
                lead["email"] = emails[0]

            if use_pagespeed:
                lead["pagespeed"] = pagespeed_score(final_url, pagespeed_key)
                if lead["pagespeed"] and int(lead["pagespeed"]) < 50:
                    issues.append("low_pagespeed")

    score = sum(ISSUE_WEIGHT[i] for i in issues)
    # Established businesses (many reviews) can afford a website and have something to lose.
    reviews = int(float(lead["reviews"] or 0))
    score += min(reviews // 10, 20)
    if lead["email"] or lead["phone"]:
        score += 5
    lead["issues"] = ";".join(issues)
    lead["score"] = str(score)
    lead["audited"] = now()


def cmd_audit(args, cfg, leads, leads_path) -> None:
    todo = [l for l in leads.values() if not l["audited"] or args.force]
    use_ps = not args.no_pagespeed
    key = os.environ.get("PAGESPEED_API_KEY") or os.environ.get("GOOGLE_PLACES_API_KEY")
    for n, lead in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {lead['name']} {lead['website'] or '(no website)'}")
        audit_lead(lead, key, use_ps)
        print(f"  score={lead['score']} issues={lead['issues'] or '-'} email={lead['email'] or '-'}")
        save_leads(leads_path, leads)  # save as we go so long runs survive interruptions


# --------------------------------------------------------------------------- outreach

def render(template: str, lead: dict, cfg: dict) -> str:
    sender = cfg.get("sender", {})
    issue_keys = [i for i in lead["issues"].split(";") if i]
    bullets = "\n".join("• " + ISSUE_TEXT[i].format(**lead) for i in issue_keys[:3])
    reviews = int(float(lead["reviews"] or 0))
    reputation = (
        f"Mit {reviews} Google-Bewertungen haben Sie sich offensichtlich schon einen guten Ruf aufgebaut. "
        "Eine moderne Website sorgt dafür, dass daraus auch online neue Kunden werden.\n\n"
    ) if reviews >= 10 else ""
    values = {
        **lead,
        "issue_bullets": bullets,
        "reputation_line": reputation,
        "sender_name": sender.get("name", ""),
        "sender_company": sender.get("company", ""),
        "sender_phone": sender.get("phone", ""),
        "sender_website": sender.get("website", ""),
        "offer": cfg.get("offer", ""),
        "booking_link": cfg.get("booking_link", ""),
    }
    return template.format_map(DefaultDict(values)).strip() + "\n"


class DefaultDict(dict):
    def __missing__(self, key):
        return ""


def templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "templates"


def read_template(cfg: dict, name: str) -> tuple[str, str]:
    custom = cfg.get("templates", {}).get(name)
    path = Path(custom) if custom else templates_dir() / f"{name}.txt"
    subject, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
    return subject.removeprefix("Subject:").strip(), body


def build_message(lead: dict, cfg: dict, template: str) -> EmailMessage:
    subject_t, body_t = read_template(cfg, template)
    sender = cfg.get("sender", {})
    from_email = os.environ.get("SENDER_EMAIL") or sender.get("email")
    if not from_email:
        sys.exit("Set SENDER_EMAIL or sender.email in acquisition.json.")
    msg = EmailMessage()
    msg["Subject"] = render(subject_t, lead, cfg).strip()
    msg["From"] = formataddr((sender.get("name", ""), from_email))
    msg["To"] = lead["email"]
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[1])
    msg["List-Unsubscribe"] = f"<mailto:{from_email}?subject=Abmelden>"
    msg.set_content(render(body_t, lead, cfg))
    return msg


def smtp_connection():
    host = os.environ.get("SMTP_HOST")
    if not host:
        sys.exit("SMTP_HOST / SMTP_USER / SMTP_PASSWORD are required with --send.")
    port = int(os.environ.get("SMTP_PORT", "465"))
    ctx = ssl.create_default_context()
    server = smtplib.SMTP_SSL(host, port, context=ctx) if port == 465 else smtplib.SMTP(host, port)
    if port != 465:
        server.starttls(context=ctx)
    server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    return server


def send_batch(leads: dict, cfg: dict, args, leads_path: Path, picks: list[dict], template: str, stamp_field: str) -> None:
    drafts = Path(args.drafts)
    drafts.mkdir(exist_ok=True)
    server = smtp_connection() if args.send else None
    try:
        for lead in picks:
            msg = build_message(lead, cfg, template)
            if server:
                server.send_message(msg)
                lead[stamp_field] = now()
                if template == "initial_email":
                    lead["status"] = "contacted"
                save_leads(leads_path, leads)
                print(f"sent  -> {lead['name']} <{lead['email']}>")
                time.sleep(args.delay)
            else:
                path = drafts / f"{template}-{re.sub(r'[^A-Za-z0-9]+', '_', lead['name'])[:40]}.eml"
                path.write_bytes(bytes(msg))
                print(f"draft -> {path}")
    finally:
        if server:
            server.quit()
    if not args.send:
        print(f"\n{len(picks)} drafts written to {drafts}/ (nothing sent). Re-run with --send to send.")


def daily_sent(leads: dict) -> int:
    today = datetime.now().date().isoformat()
    return sum(l["contacted_at"].startswith(today) + l["followup_at"].startswith(today) for l in leads.values())


def cmd_outreach(args, cfg, leads, leads_path) -> None:
    budget = max(0, args.limit - daily_sent(leads)) if args.send else args.limit
    min_score = cfg.get("min_score", 20)
    picks = [
        l for l in leads.values()
        if l["status"] == "new" and l["email"] and l["audited"] and int(l["score"] or 0) >= min_score
    ]
    picks.sort(key=lambda l: -int(l["score"]))
    send_batch(leads, cfg, args, leads_path, picks[:budget], "initial_email", "contacted_at")


def cmd_followup(args, cfg, leads, leads_path) -> None:
    budget = max(0, args.limit - daily_sent(leads)) if args.send else args.limit
    cutoff = datetime.now() - timedelta(days=args.days)
    picks = [
        l for l in leads.values()
        if l["status"] == "contacted" and l["contacted_at"] and not l["followup_at"]
        and datetime.fromisoformat(l["contacted_at"]) <= cutoff
    ]
    send_batch(leads, cfg, args, leads_path, picks[:budget], "followup_email", "followup_at")


# --------------------------------------------------------------------------- call

def cmd_call(args, cfg, leads, leads_path) -> None:
    """Outbound call via an ElevenLabs agent for leads that have a phone but no email."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID") or cfg.get("elevenlabs", {}).get("agent_id")
    phone_id = os.environ.get("ELEVENLABS_PHONE_NUMBER_ID") or cfg.get("elevenlabs", {}).get("agent_phone_number_id")
    if args.dial and not (api_key and agent_id and phone_id):
        sys.exit("ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and ELEVENLABS_PHONE_NUMBER_ID are required with --dial.")
    hour = datetime.now().hour
    if args.dial and not 9 <= hour < 18:
        sys.exit("Outside calling hours (09:00-18:00). Nothing dialed.")
    min_score = cfg.get("min_score", 20)
    picks = [
        l for l in leads.values()
        if l["status"] == "new" and l["phone"] and not l["email"] and not l["called_at"]
        and l["audited"] and int(l["score"] or 0) >= min_score
    ]
    picks.sort(key=lambda l: -int(l["score"]))
    for lead in picks[:args.limit]:
        issue_keys = [i for i in lead["issues"].split(";") if i]
        variables = {
            "business_name": lead["name"],
            "issues": " ".join(ISSUE_TEXT[i].format(**lead) for i in issue_keys[:2]),
            "sender_name": cfg.get("sender", {}).get("name", ""),
            "sender_company": cfg.get("sender", {}).get("company", ""),
            "offer": cfg.get("offer", ""),
        }
        if not args.dial:
            print(f"would call {lead['name']} {lead['phone']} with {json.dumps(variables, ensure_ascii=False)}")
            continue
        resp = http_json(
            "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
            {
                "agent_id": agent_id,
                "agent_phone_number_id": phone_id,
                "to_number": lead["phone"],
                "conversation_initiation_client_data": {"dynamic_variables": variables},
            },
            {"xi-api-key": api_key},
        )
        lead["called_at"] = now()
        lead["status"] = "called"
        lead["notes"] = (lead["notes"] + f" conversation_id={resp.get('conversation_id', '')}").strip()
        save_leads(leads_path, leads)
        print(f"called {lead['name']} -> {resp.get('conversation_id')}")
        time.sleep(args.delay)


# --------------------------------------------------------------------------- report

def cmd_report(args, cfg, leads, leads_path) -> None:
    by_status: dict[str, int] = {}
    for l in leads.values():
        by_status[l["status"] or "new"] = by_status.get(l["status"] or "new", 0) + 1
    print(f"Leads: {len(leads)}")
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {status:16} {count}")
    print("\nTop 10 open leads:")
    open_leads = [l for l in leads.values() if l["status"] not in STOP_STATUSES and l["audited"]]
    for l in sorted(open_leads, key=lambda l: -int(l["score"] or 0))[:10]:
        contact = l["email"] or l["phone"] or "-"
        print(f"  {l['score']:>3}  {l['name'][:35]:35}  {contact:30}  {l['issues']}")


# --------------------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--leads", default="leads.csv", help="lead database (CSV)")
    p.add_argument("--config", default="acquisition.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find", help="find businesses via Google Places")
    f.add_argument("--query", help='e.g. "Friseur"')
    f.add_argument("--city", default="", help='e.g. "München"')
    f.add_argument("--max", type=int, default=60)

    a = sub.add_parser("audit", help="audit websites and score leads")
    a.add_argument("--force", action="store_true", help="re-audit already audited leads")
    a.add_argument("--no-pagespeed", action="store_true")

    for name in ("outreach", "followup", "run"):
        s = sub.add_parser(name)
        s.add_argument("--send", action="store_true", help="actually send (default: write drafts)")
        s.add_argument("--limit", type=int, default=20, help="max emails per day")
        s.add_argument("--delay", type=float, default=45, help="seconds between emails")
        s.add_argument("--drafts", default="drafts")
        if name in ("followup", "run"):
            s.add_argument("--days", type=int, default=5, help="days before follow-up")
        if name == "run":
            s.add_argument("--max", type=int, default=60)
            s.add_argument("--no-pagespeed", action="store_true")
            s.add_argument("--force", action="store_true")
            s.add_argument("--query", default=None)
            s.add_argument("--city", default="")

    c = sub.add_parser("call", help="ElevenLabs outbound calls for leads without email")
    c.add_argument("--dial", action="store_true", help="actually dial (default: preview)")
    c.add_argument("--limit", type=int, default=10)
    c.add_argument("--delay", type=float, default=30)

    sub.add_parser("report", help="pipeline summary")

    args = p.parse_args()
    leads_path = Path(args.leads)
    cfg = load_config(Path(args.config))
    leads = load_leads(leads_path)

    if args.cmd == "find":
        cmd_find(args, cfg, leads)
        save_leads(leads_path, leads)
    elif args.cmd == "audit":
        cmd_audit(args, cfg, leads, leads_path)
    elif args.cmd == "outreach":
        cmd_outreach(args, cfg, leads, leads_path)
    elif args.cmd == "followup":
        cmd_followup(args, cfg, leads, leads_path)
    elif args.cmd == "call":
        cmd_call(args, cfg, leads, leads_path)
    elif args.cmd == "report":
        cmd_report(args, cfg, leads, leads_path)
    elif args.cmd == "run":
        if os.environ.get("GOOGLE_PLACES_API_KEY") and (args.query or cfg.get("queries")):
            cmd_find(args, cfg, leads)
            save_leads(leads_path, leads)
        cmd_audit(args, cfg, leads, leads_path)
        cmd_outreach(args, cfg, leads, leads_path)
        cmd_followup(args, cfg, leads, leads_path)
        cmd_report(args, cfg, leads, leads_path)


if __name__ == "__main__":
    main()
