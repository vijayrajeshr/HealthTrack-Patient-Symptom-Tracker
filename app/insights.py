from collections import defaultdict
from datetime import datetime, timedelta


def build_insights(records):
    """
    Computes summary insights from a list of symptom records:
    - total_entries: total count
    - average_severity: rounded to 1 decimal
    - weekly_averages: list of {week_start, average_severity, entries} sorted oldest first
    - most_common: top 5 symptoms by count (ties broken alphabetically)
    - highest_entry: entry with highest severity (ties go to latest date)
    - trend: comparison of the last two weeks ('improving', 'worsening', 'steady', or None)
    """
    if not records:
        return {
            "total_entries": 0,
            "average_severity": 0.0,
            "weekly_averages": [],
            "most_common": [],
            "highest_entry": None,
            "trend": None,
            "message": "No symptom entries recorded for this period.",
        }

    total_entries = len(records)
    avg_severity = round(sum(r["severity"] for r in records) / total_entries, 1)

    # 1. Weekly Averages
    # Group by Monday of ISO week
    weeks_dict = defaultdict(list)
    for r in records:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
            monday = d - timedelta(days=d.weekday())
            week_key = monday.isoformat()
            weeks_dict[week_key].append(r["severity"])
        except (ValueError, KeyError):
            continue

    weekly_averages = []
    for week_start in sorted(weeks_dict.keys()):
        severities = weeks_dict[week_start]
        count = len(severities)
        weekly_averages.append({
            "week_start": week_start,
            "average_severity": round(sum(severities) / count, 1),
            "entries": count,
        })

    # 2. Most Common Symptoms (Top 5)
    symptom_data = defaultdict(list)
    for r in records:
        sym = r.get("symptom")
        if sym:
            symptom_data[sym].append(r["severity"])

    # Sort primarily by frequency desc, secondarily by symptom name asc
    sorted_symptoms = sorted(
        symptom_data.items(),
        key=lambda item: (-len(item[1]), item[0])
    )

    most_common = []
    for sym_name, severities in sorted_symptoms[:5]:
        count = len(severities)
        most_common.append({
            "symptom": sym_name,
            "count": count,
            "average_severity": round(sum(severities) / count, 1),
        })

    # 3. Highest Entry
    # Max severity; tie-break: latest date, then latest timestamp
    highest_entry = max(
        records,
        key=lambda r: (
            r.get("severity", 0),
            r.get("date", ""),
            r.get("timestamp", ""),
        ),
        default=None,
    )

    # 4. Trend Analysis
    trend = None
    if len(weekly_averages) >= 2:
        last_week = weekly_averages[-1]["average_severity"]
        prev_week = weekly_averages[-2]["average_severity"]
        diff = last_week - prev_week
        if diff <= -0.5:
            trend = "improving"
        elif diff >= 0.5:
            trend = "worsening"
        else:
            trend = "steady"

    return {
        "total_entries": total_entries,
        "average_severity": avg_severity,
        "weekly_averages": weekly_averages,
        "most_common": most_common,
        "highest_entry": highest_entry,
        "trend": trend,
        "message": None,
    }
