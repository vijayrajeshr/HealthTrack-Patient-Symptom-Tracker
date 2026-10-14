import re
from datetime import date, datetime

USER_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def validate_user_id(uid):
    """
    Validates user_id:
    Must be a string of 1-40 chars containing only letters, numbers, hyphens, or underscores.
    Returns (cleaned_uid, error_message).
    """
    if not isinstance(uid, str):
        return None, "User ID is required and must be a string."
    cleaned = uid.strip()
    if not cleaned:
        return None, "User ID cannot be empty."
    if not USER_ID_REGEX.match(cleaned):
        return None, "User ID must be 1 to 40 characters using letters, numbers, hyphens, or underscores."
    return cleaned, None


def parse_date(date_str):
    """
    Parses a string into a date object if valid YYYY-MM-DD.
    Returns (date_obj, error_message).
    """
    if not isinstance(date_str, str):
        return None, "Date must be a string in YYYY-MM-DD format."
    date_str = date_str.strip()
    if len(date_str) != 10:
        return None, "Date must be in YYYY-MM-DD format."
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        return parsed, None
    except ValueError:
        return None, "Date must be a valid calendar date in YYYY-MM-DD format."


def validate_range(start_str, end_str):
    """
    Validates optional start and end date query parameters.
    Returns (start_str, end_str, errors_dict).
    """
    errors = {}
    start_date = None
    end_date = None
    clean_start = None
    clean_end = None

    if start_str is not None and str(start_str).strip() != "":
        start_date, err = parse_date(str(start_str).strip())
        if err:
            errors["start"] = err
        else:
            clean_start = start_date.isoformat()

    if end_str is not None and str(end_str).strip() != "":
        end_date, err = parse_date(str(end_str).strip())
        if err:
            errors["end"] = err
        else:
            clean_end = end_date.isoformat()

    if start_date and end_date and start_date > end_date:
        errors["range"] = "Start date must be before or equal to end date."

    if errors:
        return None, None, errors
    return clean_start, clean_end, None


def parse_severity(val):
    """
    Parses severity into integer 1-10.
    Rejects booleans, decimals, non-numeric strings, values < 1 or > 10.
    Returns (int_severity, error_message).
    """
    if isinstance(val, bool):
        return None, "Severity must be a whole number between 1 and 10."

    if isinstance(val, int):
        sev = val
    elif isinstance(val, float):
        if val.is_integer():
            sev = int(val)
        else:
            return None, "Severity must be a whole number between 1 and 10."
    elif isinstance(val, str):
        val_str = val.strip()
        try:
            # Check if integer string
            if "." in val_str:
                f_val = float(val_str)
                if f_val.is_integer():
                    sev = int(f_val)
                else:
                    return None, "Severity must be a whole number between 1 and 10."
            else:
                sev = int(val_str)
        except (ValueError, TypeError):
            return None, "Severity must be a whole number between 1 and 10."
    else:
        return None, "Severity must be a whole number between 1 and 10."

    if sev < 1 or sev > 10:
        return None, "Severity must be a whole number between 1 and 10."

    return sev, None


def validate_symptom(payload):
    """
    Validates symptom creation payload.
    Collects all errors into a dictionary keyed by field name.
    Returns (clean_dict, errors_dict).
    """
    if not isinstance(payload, dict):
        return None, {"body": "Expected a JSON object."}

    errors = {}
    clean = {}

    # user_id
    uid = payload.get("user_id")
    cleaned_uid, uid_err = validate_user_id(uid)
    if uid_err:
        errors["user_id"] = uid_err
    else:
        clean["user_id"] = cleaned_uid

    # symptom
    sym = payload.get("symptom")
    if not isinstance(sym, str):
        errors["symptom"] = "Symptom description is required and must be text."
    else:
        # Normalize: strip, collapse whitespace, lowercase
        normalized_sym = " ".join(sym.strip().split()).lower()
        if not normalized_sym:
            errors["symptom"] = "Symptom description cannot be empty."
        elif len(normalized_sym) > 80:
            errors["symptom"] = "Symptom description cannot exceed 80 characters."
        else:
            clean["symptom"] = normalized_sym

    # severity
    sev = payload.get("severity")
    if sev is None:
        errors["severity"] = "Severity is required."
    else:
        parsed_sev, sev_err = parse_severity(sev)
        if sev_err:
            errors["severity"] = sev_err
        else:
            clean["severity"] = parsed_sev

    # date
    dt_val = payload.get("date")
    if dt_val is None:
        errors["date"] = "Date is required."
    else:
        parsed_dt, dt_err = parse_date(str(dt_val).strip() if isinstance(dt_val, str) else "")
        if dt_err:
            errors["date"] = dt_err
        elif parsed_dt > date.today():
            errors["date"] = "Date cannot be in the future."
        else:
            clean["date"] = parsed_dt.isoformat()

    if errors:
        return None, errors
    return clean, {}
