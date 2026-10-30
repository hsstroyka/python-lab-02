import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.parsers import parse_csv, parse_jsonl, read_csv, read_jsonl


def test_csv(tmp_path):
    path = tmp_path / "events.csv"
    path.write_text(
        "timestamp,level,source,message\n"
        "2026-04-01T10:00:00Z,INFO,сайт,Привет\n",
        encoding="utf-8",
    )

    line_number, row = next(read_csv(str(path)))
    event = parse_csv(row)

    assert line_number == 2
    assert event["source"] == "сайт"
    assert event["message"] == "Привет"


def test_jsonl(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-01T10:00:00Z","level":"ERROR",'
        '"source":"база","message":"Ошибка"}\n',
        encoding="utf-8",
    )

    line_number, line = next(read_jsonl(str(path)))
    event = parse_jsonl(line)

    assert line_number == 1
    assert event["level"] == "ERROR"
    assert event["source"] == "база"


def test_bad_json():
    with pytest.raises(InvalidEventError, match="неверный JSON"):
        parse_jsonl("{сломанный json")


def test_missing_field():
    with pytest.raises(InvalidEventError, match="message"):
        parse_csv({
            "timestamp": "2026-04-01T10:00:00Z",
            "level": "INFO",
            "source": "app",
        })


def test_extra_csv_column():
    with pytest.raises(InvalidEventError, match="CSV"):
        parse_csv({"source": "app", None: ["лишний столбец"]})


def test_bad_date():
    with pytest.raises(InvalidTimestampError, match="timestamp"):
        parse_jsonl(
            '{"timestamp":"2026-02-30T10:00:00Z","level":"INFO",'
            '"source":"app","message":"test"}'
        )


def test_bad_source():
    with pytest.raises(InvalidEventError, match="source"):
        parse_jsonl(
            '{"timestamp":"2026-04-01T10:00:00Z","level":"INFO",'
            '"source":" ","message":"test"}'
        )


def test_bad_level():
    with pytest.raises(InvalidEventError, match="level"):
        parse_jsonl(
            '{"timestamp":"2026-04-01T10:00:00Z","level":"NOTICE",'
            '"source":"app","message":"test"}'
        )


import sys
from streamstats.__main__ import main


def test_main_analyze(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"

    path.write_text(
        '{"timestamp":"2026-04-01T12:00:00Z",'
        '"level":"INFO","source":"app","message":"Запуск"}\n',
        encoding="utf-8"
    )

    monkeypatch.setattr(sys, "argv", [
        "streamstats",
        "analyze",
        str(path),
        "--format",
        "jsonl"
    ])

    result = main()

    assert result == 0


def test_main_wrong_top(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    path.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [
        "streamstats",
        "analyze",
        str(path),
        "--format",
        "jsonl",
        "--top",
        "0"
    ])

    result = main()

    assert result == 2
