from __future__ import annotations

import pytest
from freezegun import freeze_time

from twvideo_dl.main import main

TIMESTAMP = "2000-01-02 03:04:05"


INVALID_TEST_CASES: list[tuple[str, str]] = [
    ("invalid", "Error: Invalid tweet url.\n"),
    ("https://example.com", "Error: Invalid tweet url.\n"),
    (
        "https://twitter.com/jack/status/20",
        "Error: Failed to fetch video info. Does this tweet contain of any video?\n",
    ),
    (
        "https://x.com/jack/status/311512159605649408?s=20",
        "Error: Failed to fetch video info. Does this tweet contain of any video?\n",
    ),
    (
        "https://x.com/jack/status/284779356075741184?s=20",
        "Error: Failed to fetch video info. Does this tweet contain of any video?\n",
    ),
    (
        "https://x.com/jack/status/1071575147293769728?s=20",
        "Error: Failed to fetch video info. Does this tweet contain of any video?\n",
    ),
]

VALID_TEST_CASES: list[tuple[str, str]] = [
    (
        "https://twitter.com/jack/status/630260408666882048?s=20",
        "Saved: 2000_01_02_03_04_05_000_dX06G7A6camzrcWn.mp4\n",
    ),
    (
        "https://x.com/jack/status/630260408666882048?s=20",
        "Saved: 2000_01_02_03_04_05_000_dX06G7A6camzrcWn.mp4\n",
    ),
    (
        "https://x.com/Support/status/1577730112853680128",
        "Saved: 2000_01_02_03_04_05_000_dX06G7A6camzrcWn.mp4\n",
    ),
    (
        "https://x.com/aespa_official/status/1577282815250427907",
        "Saved: 2000_01_02_03_04_05_000_dX06G7A6camzrcWn.mp4\n",
    ),
]


@pytest.mark.parametrize(("url", "err"), INVALID_TEST_CASES)
@freeze_time(TIMESTAMP)
def test_from_arg_invalid(
    url: str,
    err: str,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", [__file__, url])
    with pytest.raises(SystemExit) as ext:
        main()
    captured = capfd.readouterr()
    assert ext.value.code == 1
    assert not captured.out
    assert captured.err == err


@pytest.mark.parametrize(("url", "out"), VALID_TEST_CASES)
@freeze_time(TIMESTAMP)
def test_from_arg_valid(
    url: str,
    out: str,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", [__file__, url])
    main()
    captured = capfd.readouterr()
    assert captured.out == out
    assert not captured.err


@pytest.mark.parametrize(("url", "err"), INVALID_TEST_CASES[:1])
@freeze_time(TIMESTAMP)
def test_from_stdin_invalid(
    url: str,
    err: str,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: url)
    with pytest.raises(SystemExit) as ext:
        main()
    captured = capfd.readouterr()
    assert ext.value.code == 1
    assert not captured.out
    assert captured.err == err


@pytest.mark.parametrize(("url", "out"), VALID_TEST_CASES[:1])
@freeze_time(TIMESTAMP)
def test_from_stdin_valid(
    url: str,
    out: str,
    capfd: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: url)
    main()
    captured = capfd.readouterr()
    assert captured.out == out
    assert not captured.err
