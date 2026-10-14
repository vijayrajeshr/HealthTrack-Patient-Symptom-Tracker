import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
from datetime import datetime, timezone


class SymptomRepository:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensures parent directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_data(self):
        """
        Reads records from JSON file.
        If file is missing, returns empty list.
        If file is corrupt, renames to .corrupt and resets with [].
        """
        if not self.path.exists():
            return []

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                if not isinstance(data, list):
                    raise ValueError("Stored data is not a list")
                return data
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            # Corrupt file recovery
            corrupt_path = self.path.with_name(f"{self.path.name}.corrupt")
            try:
                if corrupt_path.exists():
                    corrupt_path.unlink()
                self.path.rename(corrupt_path)
            except OSError:
                pass
            self._write_data([])
            return []

    def _write_data(self, data):
        """
        Atomically writes data to the JSON file using a temp file and os.replace.
        """
        self._ensure_storage()
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                delete=False,
                prefix="symptoms_",
                suffix=".tmp",
            ) as f:
                temp_file = f.name
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_file, self.path)
        except Exception:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
            raise

    def add(self, user_id, symptom, severity, date):
        """
        Adds a new symptom entry and persists atomically.
        Returns the created record.
        """
        record = {
            "id": secrets.token_hex(6),  # 12-char hex
            "user_id": user_id,
            "symptom": symptom,
            "severity": int(severity),
            "date": date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self._lock:
            data = self._read_data()
            data.append(record)
            self._write_data(data)

        return record

    def list(self, user_id, start=None, end=None):
        """
        Lists symptoms for a user, optionally filtered by inclusive date range.
        Sorted newest first (date descending, timestamp descending).
        """
        with self._lock:
            data = self._read_data()

        results = []
        for item in data:
            if item.get("user_id") != user_id:
                continue
            item_date = item.get("date", "")
            if start and item_date < start:
                continue
            if end and item_date > end:
                continue
            results.append(item)

        # Sort newest first
        results.sort(key=lambda r: (r.get("date", ""), r.get("timestamp", "")), reverse=True)
        return results

    def delete(self, user_id, record_id):
        """
        Deletes a record if found for user_id.
        Returns True if deleted, False if not found.
        """
        with self._lock:
            data = self._read_data()
            target_idx = None
            for idx, item in enumerate(data):
                if item.get("id") == record_id and item.get("user_id") == user_id:
                    target_idx = idx
                    break

            if target_idx is None:
                return False

            data.pop(target_idx)
            self._write_data(data)
            return True
