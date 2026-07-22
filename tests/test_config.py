import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resolvevoxtral import config


def test_load_config_missing_file_returns_empty_dict(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert config.load_config() == {}


def test_save_then_load_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config.set_api_key("sk-test-123")
    assert config.get_api_key() == "sk-test-123"


def test_corrupt_json_treated_as_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config.get_config_dir().mkdir(parents=True, exist_ok=True)
    config.get_config_path().write_text("{not valid json", encoding="utf-8")
    assert config.load_config() == {}


def test_get_api_key_missing_key_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config.save_config({"schema_version": 1})
    assert config.get_api_key() is None
