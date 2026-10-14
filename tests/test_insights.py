from app.insights import build_insights


def test_insights_empty():
    res = build_insights([])
    assert res["total_entries"] == 0
    assert res["average_severity"] == 0.0
    assert res["weekly_averages"] == []
    assert res["most_common"] == []
    assert res["highest_entry"] is None
    assert res["trend"] is None
    assert res["message"] is not None


def test_insights_averages_and_totals():
    records = [
        {"symptom": "headache", "severity": 4, "date": "2026-10-01", "timestamp": "T1"},
        {"symptom": "fatigue", "severity": 7, "date": "2026-10-02", "timestamp": "T2"},
    ]
    res = build_insights(records)
    assert res["total_entries"] == 2
    assert res["average_severity"] == 5.5
    assert res["message"] is None


def test_insights_weekly_grouping():
    # 2026-10-05 is Monday, 2026-10-07 is Wednesday (same week: Monday 2026-10-05)
    # 2026-10-12 is Monday (next week)
    records = [
        {"symptom": "headache", "severity": 4, "date": "2026-10-05", "timestamp": "T1"},
        {"symptom": "headache", "severity": 6, "date": "2026-10-07", "timestamp": "T2"},
        {"symptom": "fatigue", "severity": 8, "date": "2026-10-12", "timestamp": "T3"},
    ]
    res = build_insights(records)
    assert len(res["weekly_averages"]) == 2

    w1 = res["weekly_averages"][0]
    assert w1["week_start"] == "2026-10-05"
    assert w1["average_severity"] == 5.0
    assert w1["entries"] == 2

    w2 = res["weekly_averages"][1]
    assert w2["week_start"] == "2026-10-12"
    assert w2["average_severity"] == 8.0
    assert w2["entries"] == 1


def test_insights_most_common_ranking_and_tiebreak():
    # 6 symptoms: headache (3), fatigue (3), nausea (2), back pain (2), cough (1), fever (1)
    # tie break between headache and fatigue: alphabetically fatigue < headache!
    # nausea and back pain: back pain < nausea
    records = [
        {"symptom": "headache", "severity": 5, "date": "2026-10-01"},
        {"symptom": "headache", "severity": 5, "date": "2026-10-02"},
        {"symptom": "headache", "severity": 5, "date": "2026-10-03"},
        {"symptom": "fatigue", "severity": 4, "date": "2026-10-01"},
        {"symptom": "fatigue", "severity": 4, "date": "2026-10-02"},
        {"symptom": "fatigue", "severity": 4, "date": "2026-10-03"},
        {"symptom": "nausea", "severity": 3, "date": "2026-10-01"},
        {"symptom": "nausea", "severity": 3, "date": "2026-10-02"},
        {"symptom": "back pain", "severity": 6, "date": "2026-10-01"},
        {"symptom": "back pain", "severity": 6, "date": "2026-10-02"},
        {"symptom": "cough", "severity": 2, "date": "2026-10-01"},
        {"symptom": "fever", "severity": 8, "date": "2026-10-01"},
    ]
    res = build_insights(records)
    # Top 5 only
    assert len(res["most_common"]) == 5

    names = [item["symptom"] for item in res["most_common"]]
    # count 3: "fatigue" comes before "headache"
    assert names[0] == "fatigue"
    assert names[1] == "headache"
    # count 2: "back pain" comes before "nausea"
    assert names[2] == "back pain"
    assert names[3] == "nausea"
    # count 1: "cough" comes before "fever"
    assert names[4] == "cough"


def test_insights_highest_entry_tie_resolution():
    records = [
        {"symptom": "headache", "severity": 8, "date": "2026-10-01", "timestamp": "2026-10-01T10:00:00Z"},
        {"symptom": "migraine", "severity": 9, "date": "2026-10-02", "timestamp": "2026-10-02T10:00:00Z"},
        # Same severity 9, but later date
        {"symptom": "acute pain", "severity": 9, "date": "2026-10-05", "timestamp": "2026-10-05T10:00:00Z"},
    ]
    res = build_insights(records)
    assert res["highest_entry"]["symptom"] == "acute pain"
    assert res["highest_entry"]["date"] == "2026-10-05"


def test_insights_trend():
    # Only 1 week: no trend
    res_one_week = build_insights([
        {"symptom": "cough", "severity": 4, "date": "2026-10-05"},
    ])
    assert res_one_week["trend"] is None

    # Improving: week 1 avg 8.0, week 2 avg 6.0 (diff = -2.0 <= -0.5)
    improving_records = [
        {"symptom": "cough", "severity": 8, "date": "2026-10-05"},
        {"symptom": "cough", "severity": 6, "date": "2026-10-12"},
    ]
    assert build_insights(improving_records)["trend"] == "improving"

    # Worsening: week 1 avg 4.0, week 2 avg 6.0 (diff = +2.0 >= 0.5)
    worsening_records = [
        {"symptom": "cough", "severity": 4, "date": "2026-10-05"},
        {"symptom": "cough", "severity": 6, "date": "2026-10-12"},
    ]
    assert build_insights(worsening_records)["trend"] == "worsening"

    # Steady: week 1 avg 5.0, week 2 avg 5.2 (diff = 0.2)
    steady_records = [
        {"symptom": "cough", "severity": 5, "date": "2026-10-05"},
        {"symptom": "cough", "severity": 5, "date": "2026-10-12"},
    ]
    assert build_insights(steady_records)["trend"] == "steady"


def test_insights_skips_malformed_date_safely():
    records = [
        {"symptom": "cough", "severity": 5, "date": "not-a-date"},
        {"symptom": "cough", "severity": 7, "date": "2026-10-12"},
    ]
    res = build_insights(records)
    assert res["total_entries"] == 2
    assert len(res["weekly_averages"]) == 1
    assert res["weekly_averages"][0]["average_severity"] == 7.0

