import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .insights import build_insights
from .storage import SymptomRepository
from .validation import validate_range, validate_symptom, validate_user_id

BASE_DIR = Path(__file__).resolve().parent.parent


def error(message, status=400, details=None):
    return jsonify({"error": message, "details": details or {}}), status


def create_app(data_file=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # reject oversized bodies
    repo = SymptomRepository(data_file or os.environ.get("HEALTHTRACK_DATA", BASE_DIR / "data" / "symptoms.json"))

    def query_filters():
        uid, err = validate_user_id(request.args.get("user_id"))
        if err:
            return None, error("Invalid request.", details={"user_id": err})
        start, end, errs = validate_range(request.args.get("start"), request.args.get("end"))
        if errs:
            return None, error("Invalid date range.", details=errs)
        return (uid, start, end), None

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/about")
    def about():
        return render_template("about.html")


    @app.post("/api/symptoms")
    def add_symptom():
        payload = request.get_json(silent=True)
        if payload is None:
            return error("Request body must be valid JSON.")
        clean, errs = validate_symptom(payload)
        if errs:
            return error("Some fields need fixing.", details=errs)
        return jsonify(repo.add(**clean)), 201

    @app.get("/api/symptoms")
    def get_symptoms():
        filters, err = query_filters()
        if err:
            return err
        records = repo.list(*filters)
        return jsonify({"count": len(records), "symptoms": records})

    @app.delete("/api/symptoms/<record_id>")
    def delete_symptom(record_id):
        uid, err = validate_user_id(request.args.get("user_id"))
        if err:
            return error("Invalid request.", details={"user_id": err})
        if not repo.delete(uid, record_id):
            return error("Entry not found.", 404)
        return "", 204

    @app.get("/api/insights")
    def get_insights():
        filters, err = query_filters()
        if err:
            return err
        return jsonify(build_insights(repo.list(*filters)))

    @app.errorhandler(404)
    def not_found(_):
        return error("Not found.", 404)

    @app.errorhandler(405)
    def bad_method(_):
        return error("Method not allowed.", 405)

    @app.errorhandler(413)
    def too_big(_):
        return error("Request body is too large.", 413)

    return app
