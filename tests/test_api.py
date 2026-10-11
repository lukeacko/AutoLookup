import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autolookup"))
from api import VINDataError, retry, validate_vin


def test_validate_vin_normalises_case_and_whitespace():
    assert validate_vin(" 1hgcm82633a004352 ") == "1HGCM82633A004352"


@pytest.mark.parametrize(
    "vin",
    [
        "SHORTVIN",
        "1HGCM82633A00435I",
        "1HGCM82633A00435O",
        "1HGCM82633A00435Q",
    ],
)
def test_validate_vin_rejects_invalid_values(vin):
    with pytest.raises(VINDataError):
        validate_vin(vin)


def test_retry_returns_after_transient_failure():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("temporary")
        return "ok"

    assert retry(flaky, attempts=3, delay=0, backoff=1, exceptions=(RuntimeError,)) == "ok"
    assert calls["count"] == 2


def test_retry_raises_after_final_attempt():
    calls = {"count": 0}

    def always_fails():
        calls["count"] += 1
        raise RuntimeError("still broken")

    with pytest.raises(RuntimeError):
        retry(always_fails, attempts=3, delay=0, backoff=1, exceptions=(RuntimeError,))

    assert calls["count"] == 3
