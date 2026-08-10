"""
Fetchers for each job source. Each function returns a list of dicts with a
common shape:

{
    "id": str,          # stable unique id (used for dedup / "seen" tracking)
    "title": str,
    "company": str,
    "location": str,
    "url": str,
    "description": str, # plain text, used for scoring
    "source": str,
}
"""
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
import re

HEADERS = {"User-Agent": "job-agent/1.0 (personal job search tool)"}


def _get_json(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_text(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _strip_html(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_greenhouse(companies):
    jobs = []
    for slug in companies:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        try:
            data = _get_json(url)
        except Exception as e:
            print(f"[greenhouse] skip {slug}: {e}")
            continue
        for j in data.get("jobs", []):
            jobs.append({
                "id": f"greenhouse:{slug}:{j['id']}",
                "title": j.get("title", ""),
                "company": slug,
                "location": (j.get("location") or {}).get("name", ""),
                "url": j.get("absolute_url", ""),
                "description": _strip_html(j.get("content", "")),
                "source": "Greenhouse",
            })
        time.sleep(0.3)
    return jobs


def fetch_lever(companies):
    jobs = []
    for slug in companies:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            data = _get_json(url)
        except Exception as e:
            print(f"[lever] skip {slug}: {e}")
            continue
        for j in data:
            cats = j.get("categories", {})
            jobs.append({
                "id": f"lever:{slug}:{j.get('id')}",
                "title": j.get("text", ""),
                "company": slug,
                "location": cats.get("location", ""),
                "url": j.get("hostedUrl", ""),
                "description": _strip_html(j.get("descriptionPlain") or j.get("description", "")),
                "source": "Lever",
            })
        time.sleep(0.3)
    return jobs


def fetch_remoteok(keywords):
    url = "https://remoteok.com/api"
    try:
        data = _get_json(url)
    except Exception as e:
        print(f"[remoteok] error: {e}")
        return []
    jobs = []
    kw_lower = [k.lower() for k in keywords]
    for j in data:
        if not isinstance(j, dict) or "id" not in j or "position" not in j:
            continue  # first item is a legal notice, not a job
        title = j.get("position", "")
        desc = _strip_html(j.get("description", ""))
        tags = " ".join(j.get("tags", []))
        haystack = f"{title} {tags}".lower()
        if not any(k in haystack for k in kw_lower):
            continue
        jobs.append({
            "id": f"remoteok:{j['id']}",
            "title": title,
            "company": j.get("company", ""),
            "location": j.get("location", "Remote"),
            "url": j.get("url", ""),
            "description": desc,
            "source": "RemoteOK",
        })
    return jobs


def fetch_wwr(categories):
    """We Work Remotely RSS feeds, e.g. 'remote-project-management-jobs'."""
    jobs = []
    for cat in categories:
        url = f"https://weworkremotely.com/categories/{cat}.rss"
        try:
            xml_text = _get_text(url)
            root = ET.fromstring(xml_text)
        except Exception as e:
            print(f"[wwr] skip {cat}: {e}")
            continue
        for item in root.findall(".//item"):
            link = item.findtext("link", "")
            title_full = item.findtext("title", "")
            desc = _strip_html(item.findtext("description", ""))
            # WWR titles are usually "Company: Job Title"
            company, _, title = title_full.partition(":")
            if not title:
                title, company = company, ""
            jobs.append({
                "id": f"wwr:{link}",
                "title": title.strip() or title_full,
                "company": company.strip(),
                "location": "Remote",
                "url": link,
                "description": desc,
                "source": "We Work Remotely",
            })
    return jobs
