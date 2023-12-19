from __future__ import annotations

import pytest
from freezegun import freeze_time

from twvideo.main import main

TEST_CASES: list[tuple[str, str, str]] = [
  ('', '', None),
  ('https://example.com', '', None),
  ('https://x.com/jack/status/20', '', None),
  ('https://x.com/jack/status/311512159605649408?s=20', '', None),
  ('https://x.com/jack/status/284779356075741184?s=20', '', None),
  ('https://x.com/jack/status/1071575147293769728?s=20', '', None),
  ('https://x.com/jack/status/630260408666882048?s=20', '', None),
]

TIMESTAMP = "2000-01-02 03:04:05"

@pytest.mark.parametrize("url, out, err", TEST_CASES)
@freeze_time(TIMESTAMP)
def test_from_arg(url: str, out: str, err: str, capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", lambda _: [__file__, url])
    main()
    captured = capfd.readouterr()
    assert captured.out == out  # pyre-fixme[16]
    assert captured.err == err  # pyre-fixme[16]


@pytest.mark.parametrize("url, out, err", TEST_CASES)
@freeze_time(TIMESTAMP)
def test_from_stdin(url: str, out: str, err: str, capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: url)
    main()
    captured = capfd.readouterr()
    assert captured.out == out
    assert captured.err == err
