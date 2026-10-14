from pathlib import Path
from app.storage import SymptomRepository


def test_storage_empty_init(temp_data_path):
    repo = SymptomRepository(temp_data_path)
    assert repo.list("demo") == []


def test_storage_add_and_list(repo):
    entry1 = repo.add("user1", "headache", 4, "2026-10-01")
    entry2 = repo.add("user1", "migraine", 8, "2026-10-02")

    assert len(entry1["id"]) == 12
    assert entry1["user_id"] == "user1"
    assert entry1["symptom"] == "headache"
    assert entry1["severity"] == 4
    assert entry1["date"] == "2026-10-01"
    assert "timestamp" in entry1

    results = repo.list("user1")
    assert len(results) == 2
    # Newest date first
    assert results[0]["id"] == entry2["id"]
    assert results[1]["id"] == entry1["id"]


def test_storage_persistence_across_instances(temp_data_path):
    repo1 = SymptomRepository(temp_data_path)
    repo1.add("user1", "fatigue", 5, "2026-10-05")

    repo2 = SymptomRepository(temp_data_path)
    records = repo2.list("user1")
    assert len(records) == 1
    assert records[0]["symptom"] == "fatigue"


def test_storage_user_isolation(repo):
    repo.add("alice", "nausea", 3, "2026-10-05")
    repo.add("bob", "cough", 6, "2026-10-05")

    alice_records = repo.list("alice")
    bob_records = repo.list("bob")

    assert len(alice_records) == 1
    assert alice_records[0]["symptom"] == "nausea"

    assert len(bob_records) == 1
    assert bob_records[0]["symptom"] == "cough"

    assert repo.list("charlie") == []


def test_storage_date_range_filtering(repo):
    repo.add("u1", "s1", 3, "2026-10-01")
    repo.add("u1", "s2", 5, "2026-10-05")
    repo.add("u1", "s3", 7, "2026-10-10")

    # Inclusive range
    both = repo.list("u1", start="2026-10-02", end="2026-10-06")
    assert len(both) == 1
    assert both[0]["symptom"] == "s2"

    # Start only
    from_5th = repo.list("u1", start="2026-10-05")
    assert len(from_5th) == 2
    assert [r["symptom"] for r in from_5th] == ["s3", "s2"]

    # End only
    until_5th = repo.list("u1", end="2026-10-05")
    assert len(until_5th) == 2
    assert [r["symptom"] for r in until_5th] == ["s2", "s1"]


def test_storage_delete_rules(repo):
    item = repo.add("alice", "dizziness", 4, "2026-10-08")
    record_id = item["id"]

    # Wrong user cannot delete
    assert not repo.delete("bob", record_id)
    assert len(repo.list("alice")) == 1

    # Nonexistent record cannot delete
    assert not repo.delete("alice", "nonexistent123")
    assert len(repo.list("alice")) == 1

    # Owner can delete
    assert repo.delete("alice", record_id)
    assert len(repo.list("alice")) == 0


def test_storage_corrupt_file_recovery(temp_data_path):
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    temp_data_path.write_text("{ corrupt json: [", encoding="utf-8")

    repo = SymptomRepository(temp_data_path)
    # Recovers gracefully and starts with empty list
    assert repo.list("any_user") == []

    # Corrupt file is backed up
    corrupt_file = temp_data_path.with_name(f"{temp_data_path.name}.corrupt")
    assert corrupt_file.exists()

    # Able to add new records normally
    entry = repo.add("demo", "fever", 8, "2026-10-09")
    assert len(repo.list("demo")) == 1


def test_storage_empty_file_handling(temp_data_path):
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    temp_data_path.write_text("", encoding="utf-8")
    repo = SymptomRepository(temp_data_path)
    assert repo.list("demo") == []


def test_storage_non_list_json_recovery(temp_data_path):
    temp_data_path.parent.mkdir(parents=True, exist_ok=True)
    temp_data_path.write_text('{"error": "not a list"}', encoding="utf-8")
    repo = SymptomRepository(temp_data_path)
    assert repo.list("demo") == []
    corrupt_file = temp_data_path.with_name(f"{temp_data_path.name}.corrupt")
    assert corrupt_file.exists()

