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
from serpapi import GoogleSearch
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

QUERIES = [
    "supply chain Berlin",
    "procurement Berlin",
    "logistics Berlin",
    "operations Berlin",
]

ENTRY_LEVEL_KEYWORDS = ["entry level", "junior", "graduate"]

def search_jobs(api_key):
    all_results = []
    for query in QUERIES:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": "Berlin, Germany",
            "hl": "en",
            "gl": "de",
            "api_key": "3dd91fc1be83e18b600192c57984a7ac35d28ac93a0680682c2c2c54b40a0139",
        }
        search = GoogleSearch(params)
        results = search.get_dict().get("jobs_results", [])
        print(f"Fetched {len(results)} jobs for query: {query}")
        all_results.extend(results)

    print(f"Total collected jobs (before deduplication): {len(all_results)}")

    # deduplicate by (title, company)
    seen = set()
    unique_jobs = []
    for job in all_results:
        key = (job.get("title"), job.get("company_name"))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    print(f"Unique jobs after deduplication: {len(unique_jobs)}")

    # sort by recency
    def job_age(job):
        ext = job.get("detected_extensions", {})
        if "posted_at_days_ago" in ext:
            return ext["posted_at_days_ago"]
        elif "posted_at" in ext and "day" in ext["posted_at"]:
            # fallback if "3 days ago" style string
            try:
                return int(ext["posted_at"].split()[0])
            except:
                return 999
        return 999  # assume old if unknown

    unique_jobs.sort(key=job_age)  # lowest days_ago = most recent
    return unique_jobs


def split_entry_level(jobs):
    entry, others = [], []
    for job in jobs:
        title = job.get("title", "").lower()
        if any(k in title for k in ENTRY_LEVEL_KEYWORDS):
            entry.append(job)
        else:
            others.append(job)
    return entry, others


def send_email(jobs_entry, jobs_other, sender, recipient, smtp_host, smtp_port, username, password):
    today = datetime.today().strftime("%Y-%m-%d")
    subject = f"Daily Berlin Supply Chain Digest ({today})"

    html = f"<h2>Daily digest for Berlin ({today})</h2>"

    if jobs_entry:
        html += "<h3>🎯 Entry-level roles</h3><ul>"
        for job in jobs_entry[:15]:
            html += f"<li><b>{job.get('title')}</b> - {job.get('company_name')}<br>"
            if "link" in job:
                html += f"<a href='{job['link']}'>Apply here</a></li>"
        html += "</ul>"
    else:
        html += "<p>No entry-level roles found today.</p>"

    if jobs_other:
        html += "<h3>📌 Other recent roles</h3><ul>"
        for job in jobs_other[:20]:
            html += f"<li><b>{job.get('title')}</b> - {job.get('company_name')}<br>"
            if "link" in job:
                html += f"<a href='{job['link']}'>Apply here</a></li>"
        html += "</ul>"
    else:
        html += "<p>No other roles found.</p>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, int(smtp_port), context=context) as server:
        server.login(username, password)
        server.sendmail(sender, recipient, msg.as_string())


def main():
    serpapi_key = os.environ["SERPAPI_KEY"]
    sender = os.environ["MAIL_FROM"]
    recipient = os.environ["MAIL_TO"]
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = os.environ["SMTP_PORT"]
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]

    jobs = search_jobs(serpapi_key)
    entry_jobs, other_jobs = split_entry_level(jobs)

    send_email(entry_jobs, other_jobs, sender, recipient, smtp_host, smtp_port, username, password)


if __name__ == "__main__":
    main()

          
   
