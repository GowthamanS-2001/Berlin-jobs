# Berlin Entry-Level Supply Chain Job Digest (11:00 CET/CEST)

This automation searches **Google Jobs via SerpAPI** for entry-level **Supply Chain / Procurement / Logistics Coordinator** roles in **Berlin** and emails you a daily digest with links plus a CSV attachment.

## What you'll need
- **Python 3.9+**
- A **SerpAPI API key** (free tier available): https://serpapi.com/
- An SMTP account for sending email (e.g., Gmail app password or your company SMTP).

## Setup
```bash
git clone <your-repo-or-download-zip>
cd job_automation_berlin_supplychain
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then edit with your keys
python jobs_daily.py  # test run
```

## Scheduling at 11:00 Europe/Berlin (CET/CEST)

### Linux / macOS (cron)
Edit your crontab:
```bash
crontab -e
```
Add this line (ensures Berlin timezone; adjust python path as needed):
```bash
TZ=Europe/Berlin
0 11 * * * /usr/bin/env bash -lc 'cd /path/to/job_automation_berlin_supplychain && . .venv/bin/activate && python jobs_daily.py >> cron.log 2>&1'
```

### Windows (Task Scheduler)
- Action: Start a program
- Program/script: `python`
- Add arguments: `C:\path\to\jobs_daily.py`
- Start in: folder containing `jobs_daily.py`
- Trigger: Daily at 11:00
- Ensure environment variables in `.env` are present in that folder.

## Notes & Tips
- The script uses a heuristic for "entry level" (title/description contains: entry, junior, werkstudent, trainee, associate, graduate). You can tweak `ENTRY_LEVEL_PATTERN`.
- It also boosts roles with supply chain/procurement/logistics coordinator terms.
- Google Jobs results vary; this avoids scraping protected sites like LinkedIn and relies on SerpAPI's terms.
- Want to watch more companies? Add custom keyword lines like `site:hellofresh.com careers supply chain` to `KEYWORDS` in the script.

## Uninstall
Remove the cron entry / scheduled task and delete the folder.
