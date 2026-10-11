import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autolookup"))
import historyUtils


def test_save_and_load_history(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr(historyUtils, "HISTORY_PATH", str(history_file))

    expected = [{"vin": "1HGCM82633A004352", "data": {"make": "Honda"}}]
    historyUtils.save_history(expected)

    assert historyUtils.load_history() == expected


def test_get_cached_vin_prefers_latest_entry(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr(historyUtils, "HISTORY_PATH", str(history_file))

    vin = "1HGCM82633A004352"
    historyUtils.save_history([
        {"vin": vin, "data": {"version": 1}},
        {"vin": vin, "data": {"version": 2}},
    ])

    assert historyUtils.get_cached_vin(vin) == {"version": 2}
