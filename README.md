# HealthTrack — Patient Symptom Tracker

A modern, resilient web application that enables patients to log daily symptoms, track longitudinal health patterns, and receive weekly insights.

Built for the **Aiden AI Take-Home Assessment** (Python · AIML · GenAI).

---

## Candidate Information
* **Name:** Vijay Rajesh R
* **GitHub:** [https://github.com/vijayrajeshr](https://github.com/vijayrajeshr)
* **LinkedIn:** [https://www.linkedin.com/in/vijayrajeshr](https://www.linkedin.com/in/vijayrajeshr)
* **Portfolio:** [https://vijayrajeshr.vercel.app/](https://vijayrajeshr.vercel.app/)

---

## Requirements Coverage Matrix

| Category | Requirement | Implementation Status | Location |
|---|---|---|---|
| **Must** | Log symptoms with severity (1–10) and date with input validation | **Complete** | `POST /api/symptoms`, [`app/validation.py`](app/validation.py) |
| **Must** | Data model: user ID, symptom, severity, timestamp; file persistence | **Complete** | [`app/storage.py`](app/storage.py), `data/symptoms.json` |
| **Should**| Retrieve user symptoms filtered by date range | **Complete** | `GET /api/symptoms?user_id=&start=&end=` |
| **Should**| Insights: average severity per week, top symptoms, trends | **Complete** | `GET /api/insights?user_id=&start=&end=`, [`app/insights.py`](app/insights.py) |
| **Must** | Input validation and error handling on all inputs | **Complete** | Field-level error dictionary, HTTP 400/404/405/413 |
| **Could** | Simple, polished web UI using a framework | **Complete** | Flask + Jinja2 + Vanilla CSS/JS (Tracker & About pages) |

---

## Quickstart

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.11)

### 2. Setup & Run
```bash
# Clone the repository and navigate into the project
cd TakeHomeAssessment

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

### 3. Seed Demo Data (Optional)
To populate 4 weeks of realistic sample symptom data for user `demo`:
```bash
python scripts/seed_demo.py demo
```

### 4. Run Automated Tests
```bash
pytest
```
*Executes all 46 automated tests across validation, storage, insights, and API integration.*

---

## API Specification

All API responses are formatted as JSON. Errors always follow a consistent structure:
```json
{
  "error": "Some fields need fixing.",
  "details": {
    "severity": "Severity must be a whole number between 1 and 10."
  }
}
```

| Method | Path | Description | Status Codes |
|---|---|---|---|
| `GET` | `/` | Web application symptom tracker dashboard | `200` |
| `GET` | `/about` | Architecture, developer profile, and project overview | `200` |
| `POST` | `/api/symptoms` | Log a symptom (`{user_id, symptom, severity, date}`) | `201`, `400`, `413` |
| `GET` | `/api/symptoms` | Retrieve symptoms (`?user_id=&start=&end=`) | `200`, `400` |
| `GET` | `/api/insights` | Fetch aggregated insights (`?user_id=&start=&end=`) | `200`, `400` |
| `DELETE` | `/api/symptoms/<id>` | Delete an entry (`?user_id=`) | `204`, `400`, `404` |

---

## Project Structure

```
TakeHomeAssessment/
├── app/
│   ├── __init__.py          # Flask app factory, route handlers, JSON error handlers
│   ├── validation.py        # Pure functions for input validation and normalization
│   ├── storage.py           # SymptomRepository: thread lock, atomic writes, corrupt recovery
│   ├── insights.py          # Pure functions: ISO-week grouping, top symptoms, rolling trends
│   ├── templates/
│   │   ├── index.html       # Tracker dashboard template
│   │   └── about.html       # About page with developer profile & architecture
│   └── static/
│       ├── style.css        # Responsive styling, accessible 10-step color ramp, dark theme
│       └── app.js           # Client-side reactivity, AJAX calls, form validation, toasts
├── data/
│   ├── .gitkeep             # Git keep placeholder
│   └── symptoms.json        # File persistence storage (gitignored)
├── scripts/
│   └── seed_demo.py         # 4-week sample data generator for demos
├── tests/
│   ├── conftest.py          # Pytest fixtures and isolated temporary directories
│   ├── test_validation.py   # Boundary tests, accept/reject table, normalization, future dates
│   ├── test_storage.py      # CRUD, thread safety, date filtering, corrupt file recovery
│   ├── test_insights.py     # Aggregations, rankings, tie-breakers, 2-week trends
│   └── test_api.py          # HTTP status codes (200, 201, 204, 400, 404, 405, 413)
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Minimal production & testing dependencies (Flask, pytest)
├── run.py                   # Development entrypoint
├── README.md                # Comprehensive documentation
└── .gitignore               # Ignores .venv, cache, data/*.json, *.corrupt
```

---

## Key Architectural Decisions

1. **Repository Pattern (`app/storage.py`):**
   Routes never interact with the filesystem directly. If the persistence layer is migrated to SQLite or PostgreSQL later, only `SymptomRepository` changes; business logic and routes remain untouched.
2. **Atomic Writes & Resilient Persistence:**
   File writes use `tempfile.NamedTemporaryFile` + `os.fsync()` + `os.replace()`, preventing half-written or corrupt files if a crash occurs mid-write. Guarded by a Python `threading.Lock()`.
3. **Self-Healing Corruption Recovery:**
   If `data/symptoms.json` is corrupted or contains invalid JSON, the repository automatically archives the damaged file as `symptoms.json.corrupt`, writes an empty list `[]`, and continues serving requests without crashing.
4. **All-Errors-At-Once Validation (`app/validation.py`):**
   Instead of failing on the first invalid field, all payload fields are validated together. The UI highlights each problematic input simultaneously.
5. **Data Normalization:**
   Symptom strings are trimmed, internal whitespace collapsed, and converted to lowercase (e.g. `"  Tension   Headache  "` → `"tension headache"`), ensuring consistent aggregation in insights.
6. **Pure Functional Insights (`app/insights.py`):**
   * Groups dates into ISO-8601 calendar weeks (starting on Monday).
   * Identifies the top 5 symptoms with deterministic alphabetical tie-breaking.
   * Calculates rolling two-week trends (changes $\ge 0.5$ indicate `improving` or `worsening`, otherwise `steady`).
7. **Zero-Build Vanilla Frontend:**
   Uses native HTML5, CSS3, and JavaScript with no npm build step or bundler overhead. Includes accessible radio controls (`role="radiogroup"`), keyboard navigation, dynamic autocomplete, and toast alerts.

---

## Automated Test Suite

The test suite contains **46 automated tests** executed via `pytest`:
* **Validation Tests (`test_validation.py`):** Accept/reject table for severity integers/strings/decimals, future date blocking, user ID regex, and multi-error responses.
* **Storage Tests (`test_storage.py`):** File roundtrips, multi-instance persistence, user data isolation, date filtering, and corrupt-file fallback.
* **Insights Tests (`test_insights.py`):** Empty datasets, ISO-week calculations, frequency ordering with tie-breakers, and 2-week trends.
* **API Tests (`test_api.py`):** End-to-end HTTP endpoints, status codes (200, 201, 204, 400, 404, 405, 413), and payload size limits.

Run all tests:
```bash
pytest -v
```

---

## AI Usage Disclosure

Per the assessment guidelines, here is a transparent disclosure of AI tool usage:

* **Tools Used:** Antigravity AI Coding Assistant / Gemini.
* **What AI Touched:**
  * Drafting the initial architecture, file organization, and test strategy.
  * Scaffolding boilerplate for pure functions in `validation.py`, `storage.py`, and `insights.py`.
  * Generating the 46 unit and integration test fixtures in `tests/`.
  * Suggesting UI styling utilities and color ramps for the severity scale.
* **What I Verified and Changed:**
  * Verified all edge cases: boundary checks for severity (blocking `True`/`False`, decimals, negative numbers, and `> 10`).
  * Enforced date rules ensuring future dates are strictly rejected.
  * Verified the atomic file swap implementation (`os.replace`) and corrupt file recovery logic by writing invalid JSON directly to disk.
  * Added the About page with candidate portfolio links and Aiden AI assessment accreditation.
  * Confirmed 100% test pass rate locally across all 46 tests.

---

## Video Demo Walkthrough Guide (Max 8 Minutes)

When recording your narrated video demo with webcam on, use this 7-step checklist:

| Timestamp | Section | Talking Points & Actions |
|---|---|---|
| **0:00 - 1:00** | **Introduction** | State your name (Vijay Rajesh R), introduce HealthTrack, and highlight the clean project structure (`app/`, `tests/`, `data/`). |
| **1:00 - 2:00** | **Run & Demo Seed** | Show terminal: activate `.venv`, run `python run.py`, run `python scripts/seed_demo.py demo`. Open `http://127.0.0.1:5000`. |
| **2:00 - 3:30** | **Symptom Logging & UI** | Log a symptom (e.g. `migraine`, severity `7`, today's date). Show it appear in Entries and immediately update the Insights section. |
| **3:30 - 4:30** | **Validation & Error Handling** | Demonstrate error handling: try submitting an empty symptom, severity without selection, or a future date. Point out the simultaneous field-level error messages. |
| **4:30 - 5:30** | **Filtering & Insights** | Use the "From" and "To" date range pickers to filter entries. Highlight the Weekly Average Severity bars, Top Symptoms frequency, and the 2-week Trend indicator. |
| **5:30 - 6:30** | **Test Suite Execution** | Switch to terminal and run `pytest -v`. Show all 46 tests passing rapidly. Mention storage atomic writes, concurrency locks, and corrupt-file recovery. |
| **6:30 - 7:30** | **About Page & Decisions** | Click into the **About** page (`/about`). Show the system architecture breakdown, developer profile card, and explain key design decisions (Repository pattern, zero-build simplicity). |
| **7:30 - 8:00** | **Wrap Up** | Conclude by referencing the AI Usage section in the README and expressing enthusiasm for the role at Aiden AI. |
