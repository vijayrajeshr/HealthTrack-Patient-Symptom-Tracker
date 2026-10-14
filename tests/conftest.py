import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.storage import SymptomRepository


@pytest.fixture
def temp_data_path(tmp_path):
    return tmp_path / "test_symptoms.json"


@pytest.fixture
def repo(temp_data_path):
    return SymptomRepository(temp_data_path)


@pytest.fixture
def app(temp_data_path):
    flask_app = create_app(data_file=temp_data_path)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
