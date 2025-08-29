#!/usr/bin/env python3
"""
Daily job search + emailer for entry-level Supply Chain / Procurement / Logistics Coordinator roles in Berlin.
- Searches Google Jobs via SerpAPI.
- Filters for entry-level signals.
- Emails you a digest and attaches a CSV.

Setup:
1) pip install -r requirements.txt
2) Copy .env.example to .env and fill in values.
3) Run: python jobs_daily.py
4) Schedule (cron) at 11:00 Europe/Berlin.
"""
import os
import sys
import csv
import re
import smtplib
import ssl
import serpapi
from datetime import datetime, timezone, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from dotenv import load_dotenv
ENTRY_LEVEL_PATTERN = re.compile(r'\\b(entry|junior|werkstudent|trainee|associate|graduate)\\b', re.IGNORECASE)
# Words to gently prefer (not strict filter), boost if present
PREFERRED_TERMS = re.compile(r'\\b(supply\\s*chain|procurement|logistics?\\s*coordinat(or|ion))\\b', re.IGNORECASE)

KEYWORDS = [
    "entry level supply chain",
    "junior supply chain",
    "entry level procurement",
    "junior procurement",
    "logistics coordinator",
    "junior logistics",
    "graduate supply chain",
]

LOCATION = "Berlin, Germany"
RESULTS_PER_QUERY = 20  
PAGES_PER_QUERY = 2

def search_jobs(serpapi_key: str):
    all_rows = []
    seen = set()
    for q in KEYWORDS:
        for page in range(PAGES_PER_QUERY):
            params = {
                "q": "entry-level supply chain procurement logistics coordinator jobs Berlin",
    "location": "Berlin, Germany",
    "api_key": "3dd91fc1be83e18b600192c57984a7ac35d28ac93a0680682c2c2c54b40a0139"
            }
            search = serpapi.search(params)
            results = search.as_dict()
            jobs = results.get("jobs_results", []) or []
            for j in jobs:
                title = j.get("title") or ""
                company = j.get("company_name") or j.get("company") or ""
                via = j.get("via") or ""
                desc = j.get("description") or ""
                link = None
                if isinstance(j.get("related_links"), list) and j["related_links"]:
                    link = j["related_links"][0].get("link")
                if not link:
                    link = j.get("share_link") or j.get("job_id")

                key = (title.strip(), company.strip(), link)
                if key in seen:
                    continue
                seen.add(key)

                # Basic entry-level filter: title OR description has entry-level signals
                is_entry = bool(ENTRY_LEVEL_PATTERN.search(title) or ENTRY_LEVEL_PATTERN.search(desc))
                # Accept strong keyword matches even if no explicit "entry"
                strong_match = bool(PREFERRED_TERMS.search(title))
                if not (is_entry or strong_match):
                    continue

                # Extract location and posted_at if available
                loc = j.get("location") or ""
                detected_extensions = j.get("detected_extensions") or {}
                # Normalize posted_at into a relative string if available
                posted_at = detected_extensions.get("posted_at") or detected_extensions.get("posted") or ""
                # salary, via
                salary = detected_extensions.get("salary")

                row = {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": loc.strip(),
                    "source": via,
                    "link": link,
                    "posted": posted_at,
                    "salary": salary,
                    "query": q,
                }
                all_rows.append(row)
    return all_rows

def to_html_table(rows):
    # Minimalist HTML table
    head = """<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
<tr><th>Title</th><th>Company</th><th>Location</th><th>Posted</th><th>Source</th><th>Link</th></tr>
"""
    body = []
    for r in rows:
        link_html = f'<a href="{r["link"]}">View</a>' if r.get("link") else ""
        body.append(
            f"<tr>"
            f"<td>{r.get('title','')}</td>"
            f"<td>{r.get('company','')}</td>"
            f"<td>{r.get('location','')}</td>"
            f"<td>{r.get('posted','')}</td>"
            f"<td>{r.get('source','')}</td>"
            f"<td>{link_html}</td>"
            f"</tr>"
        )
    return head + "\\n".join(body) + "</table>"

def send_email(rows, sender, recipient, smtp_host, smtp_port, username, password):
    today = date.today().isoformat()
    subject = f"Berlin Entry-Level Supply Chain Jobs — {today}"

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    intro = f"<p>Daily digest for entry-level Supply Chain / Procurement / Logistics Coordinator roles in Berlin ({today}).</p>"
    if not rows:
        html = intro + "<p>No matching roles found today.</p>"
    else:
        html = intro + to_html_table(rows)

    msg.attach(MIMEText(html, "html"))

    # Attach CSV
    csv_path = os.path.join(os.getcwd(), f"jobs_{today}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title","company","location","posted","source","link","query","salary"])
        writer.writeheader()
        writer.writerows(rows)

    with open(csv_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(csv_path)}"')
    msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.send_message(msg)

def main():
    load_dotenv()
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        print("ERROR: SERPAPI_KEY not set in environment (.env).", file=sys.stderr)
        sys.exit(1)

    sender = os.getenv("MAIL_FROM")
    recipient = os.getenv("MAIL_TO")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")
    username = os.getenv("SMTP_USERNAME") or sender
    password = os.getenv("SMTP_PASSWORD")

    if not all([sender, recipient, smtp_host, smtp_port, username, password]):
        print(key, "=", "SET" if os.getenv(key) else "MISSING")
        print("ERROR: Missing email SMTP settings in .env", file=sys.stderr)
        sys.exit(1)

    rows = search_jobs(serpapi_key)
    # Basic prioritization: prefer titles with preferred terms, then most recent (if available in text), then company name
    def score(r):
        title = r.get("title","")
        s = 0
        if PREFERRED_TERMS.search(title): s += 2
        if ENTRY_LEVEL_PATTERN.search(title): s += 1
        # posted: boost "Just posted", "1 day ago"
        posted = (r.get("posted") or "").lower()
        if "just" in posted: s += 3
        elif "day" in posted or "hour" in posted: s += 2
        return -s  # ascending sort -> highest score first by negative

    rows_sorted = sorted(rows, key=score)
    # Limit to a tidy digest
    top_rows = rows_sorted[:40]

    send_email(top_rows, sender, recipient, smtp_host, smtp_port, username, password)
    print(f"Sent {len(top_rows)} results to {recipient}.")

if __name__ == "__main__":
    main()
