from datetime import date, timedelta
import pytest

from app.validation import (
    parse_severity,
    validate_range,
    validate_symptom,
    validate_user_id,
)


def test_validate_user_id_valid():
    for valid_id in ["demo", "alice", "patient_01", "user-123", "a" * 40]:
        uid, err = validate_user_id(valid_id)
        assert err is None
        assert uid == valid_id


def test_validate_user_id_invalid():
    for invalid_id in ["", "   ", "user@id", "user space", "a" * 41, None, 12345, False]:
        uid, err = validate_user_id(invalid_id)
        assert uid is None
        assert err is not None


def test_parse_severity_valid():
    cases = [(1, 1), (10, 10), (5, 5), ("7", 7), ("1", 1), ("10", 10), (5.0, 5), ("8.0", 8)]
    for val, expected in cases:
        sev, err = parse_severity(val)
        assert err is None
        assert sev == expected


def test_parse_severity_invalid():
    cases = [0, 11, -1, 100, 5.5, "5.5", "abc", "", None, True, False, [], {}]
    for val in cases:
        sev, err = parse_severity(val)
        assert sev is None
        assert err is not None


def test_validate_range_valid():
    start, end, errs = validate_range("2026-10-01", "2026-10-10")
    assert errs is None
    assert start == "2026-10-01"
    assert end == "2026-10-10"

    # Same day
    start, end, errs = validate_range("2026-10-05", "2026-10-05")
    assert errs is None
    assert start == "2026-10-05"
    assert end == "2026-10-05"

    # Start only
    start, end, errs = validate_range("2026-10-01", None)
    assert errs is None
    assert start == "2026-10-01"
    assert end is None

    # End only
    start, end, errs = validate_range(None, "2026-10-10")
    assert errs is None
    assert start is None
    assert end == "2026-10-10"

    # Neither
    start, end, errs = validate_range(None, None)
    assert errs is None
    assert start is None
    assert end is None


def test_validate_range_invalid():
    # Start after end
    _, _, errs = validate_range("2026-10-15", "2026-10-01")
    assert errs is not None
    assert "range" in errs

    # Invalid start date format
    _, _, errs = validate_range("invalid-date", "2026-10-10")
    assert errs is not None
    assert "start" in errs

    # Impossible date (e.g. Feb 30)
    _, _, errs = validate_range("2026-02-30", "2026-10-10")
    assert errs is not None
    assert "start" in errs


def test_validate_symptom_valid():
    today_str = date.today().isoformat()
    payload = {
        "user_id": "patient_1",
        "symptom": "  Tension   Headache  ",
        "severity": "6",
        "date": today_str,
    }
    clean, errs = validate_symptom(payload)
    assert not errs
    assert clean["user_id"] == "patient_1"
    assert clean["symptom"] == "tension headache"
    assert clean["severity"] == 6
    assert clean["date"] == today_str


def test_validate_symptom_rejects_future_date():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "user_id": "patient_1",
        "symptom": "cough",
        "severity": 4,
        "date": tomorrow,
    }
    clean, errs = validate_symptom(payload)
    assert clean is None
    assert "date" in errs
    assert "future" in errs["date"].lower()


def test_validate_symptom_rejects_empty_and_long_symptom():
    today_str = date.today().isoformat()

    # Empty symptom
    clean, errs = validate_symptom({
        "user_id": "u1",
        "symptom": "   ",
        "severity": 5,
        "date": today_str,
    })
    assert "symptom" in errs

    # Exceeding 80 chars
    clean, errs = validate_symptom({
        "user_id": "u1",
        "symptom": "a" * 81,
        "severity": 5,
        "date": today_str,
    })
    assert "symptom" in errs


def test_validate_symptom_collects_all_errors_together():
    clean, errs = validate_symptom({})
    assert clean is None
    assert "user_id" in errs
    assert "symptom" in errs
    assert "severity" in errs
    assert "date" in errs


def test_validate_symptom_rejects_non_dict_body():
    clean, errs = validate_symptom(["not", "a", "dict"])
    assert clean is None
    assert "body" in errs


def test_validate_symptom_whitespace_normalization():
    today_str = date.today().isoformat()
    clean, errs = validate_symptom({
        "user_id": "test_user",
        "symptom": "Migraine \n with  Aura",
        "severity": 7,
        "date": today_str,
    })
    assert not errs
    assert clean["symptom"] == "migraine with aura"


def test_validate_symptom_string_float_severity():
    today_str = date.today().isoformat()
    # Integer-like float string
    clean, errs = validate_symptom({
        "user_id": "u1",
        "symptom": "cough",
        "severity": "5.0",
        "date": today_str,
    })
    assert not errs
    assert clean["severity"] == 5

    # Non-integer float string
    clean, errs = validate_symptom({
        "user_id": "u1",
        "symptom": "cough",
        "severity": "5.5",
        "date": today_str,
    })
    assert "severity" in errs

