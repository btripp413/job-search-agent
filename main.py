import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sources import fetch_greenhouse, fetch_lever, fetch_remoteok, fetch_wwr
from match import score_job

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_PATH = os.path.join(BASE_DIR, "data", "seen.json")
WWR_CATEGORIES = [
    "remote-project-management-jobs",
    "remote-customer-support-jobs",
]


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def collect_jobs(companies):
    jobs = []
    jobs += fetch_greenhouse(companies.get("greenhouse", []))
    jobs += fetch_lever(companies.get("lever", []))
    print(f"Greenhouse+Lever: {len(jobs)} jobs")

    remoteok_keywords = ["project manager", "customer success", "client success",
                          "implementation", "program manager", "account manager"]
    ro = fetch_remoteok(remoteok_keywords)
    print(f"RemoteOK: {len(ro)} jobs")
    jobs += ro

    wwr = fetch_wwr(WWR_CATEGORIES)
    print(f"We Work Remotely: {len(wwr)} jobs")
    jobs += wwr

    return jobs


def build_email_body(matches):
    lines = [f"{len(matches)} new job match(es) found:\n"]
    for m in matches:
        lines.append(f"[{m['score']}] {m['title']} — {m['company']} ({m['location']})")
        lines.append(f"    {m['source']}: {m['url']}")
        lines.append("")
    return "\n".join(lines)


def send_email(subject, body):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]
    to_addr = os.environ.get("NOTIFY_EMAIL", smtp_user)

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_addr], msg.as_string())


def main():
    profile = load_json(os.path.join(BASE_DIR, "resume_profile.json"), {})
    companies = load_json(os.path.join(BASE_DIR, "companies.json"), {})
    seen = set(load_json(SEEN_PATH, []))

    jobs = collect_jobs(companies)

    min_score = profile.get("min_score_to_notify", 3)
    matches = []
    for job in jobs:
        score = score_job(job, profile)
        if score is None or score < min_score:
            continue
        job["score"] = score
        matches.append(job)

    matches.sort(key=lambda j: j["score"], reverse=True)

    new_matches = [m for m in matches if m["id"] not in seen]
    print(f"Total qualifying matches: {len(matches)}; new since last run: {len(new_matches)}")

    if new_matches:
        body = build_email_body(new_matches)
        print(body)
        if os.environ.get("SMTP_USER"):
            send_email(f"Job agent: {len(new_matches)} new match(es)", body)
        else:
            print("(SMTP_USER not set — skipping email send; printed matches above instead.)")
    else:
        print("No new matches this run.")

    # mark everything we've scored above threshold as seen, so we don't
    # re-notify on the next run even if a listing lingers
    seen.update(m["id"] for m in matches)
    save_json(SEEN_PATH, sorted(seen))


if __name__ == "__main__":
    main()
