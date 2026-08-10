def score_job(job, profile):
    """Returns an integer score; higher = better fit. Returns None if the
    job should be excluded outright."""
    text = f"{job['title']} {job['description']}".lower()

    for bad in profile.get("exclude_keywords", []):
        if bad.lower() in text:
            return None

    must_have = profile.get("must_have_any", [])
    if must_have and not any(m.lower() in text for m in must_have):
        return None

    score = 0

    title_lower = job["title"].lower()
    for t in profile.get("target_titles", []):
        if t.lower() in title_lower:
            score += 4
            break
    else:
        # partial word overlap in title as a fallback
        title_words = set(title_lower.split())
        for t in profile.get("target_titles", []):
            if set(t.lower().split()) & title_words:
                score += 1
                break

    for kw in profile.get("core_keywords", []):
        if kw.lower() in text:
            score += 1

    loc = (job.get("location") or "").lower()
    loc_prefs = profile.get("location_preferences", {})
    if loc_prefs.get("prefer_remote") and "remote" in (loc + " " + job["source"]):
        score += 2
    for city in loc_prefs.get("cities", []):
        if city.lower().split(",")[0] in loc:
            score += 3

    return score
