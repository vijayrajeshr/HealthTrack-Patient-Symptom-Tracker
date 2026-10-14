import os
from pathlib import Path
import sys
from datetime import date, timedelta
import random

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.storage import SymptomRepository


SAMPLE_SYMPTOMS = [
    ("headache", 4, 7),
    ("fatigue", 3, 6),
    ("lower back pain", 5, 8),
    ("brain fog", 2, 5),
    ("joint stiffness", 3, 6),
    ("insomnia", 4, 7),
    ("nausea", 2, 5),
]


def seed(user_id="demo", num_entries=24):
    data_path = BASE_DIR / "data" / "symptoms.json"
    repo = SymptomRepository(data_path)

    today = date.today()
    random.seed(42)  # Deterministic demo set

    print(f"Seeding demo data for user '{user_id}' into {data_path}...")

    # Spread over 28 days (4 weeks)
    created = 0
    for i in range(num_entries):
        days_ago = random.randint(0, 27)
        entry_date = (today - timedelta(days=days_ago)).isoformat()
        symptom_name, min_sev, max_sev = random.choice(SAMPLE_SYMPTOMS)
        severity = random.randint(min_sev, max_sev)

        repo.add(
            user_id=user_id,
            symptom=symptom_name,
            severity=severity,
            date=entry_date,
        )
        created += 1

    print(f"Successfully seeded {created} symptom records for '{user_id}'.")


if __name__ == "__main__":
    target_user = sys.argv[1] if len(sys.argv) > 1 else "demo"
    seed(target_user)
