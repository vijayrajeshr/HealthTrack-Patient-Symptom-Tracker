from pathlib import Path
from app import create_app

app = create_app()

if __name__ == "__main__":
    data_file = Path(__file__).resolve().parent / "data" / "symptoms.json"
    if not data_file.exists() or data_file.stat().st_size <= 2:
        from scripts.seed_demo import seed
        seed("demo")
    app.run(host="127.0.0.1", port=5000, debug=True)
