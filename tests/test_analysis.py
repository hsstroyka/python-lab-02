import csv
import json
import logging

import pytest

from streamstats.analysis import analyze_files
from streamstats.errors import (
    CLIConfigError,
    InvalidEventError,
    InvalidTimestampError,
    UnsupportedFormatError,
)


def event(level="INFO", source="сайт", timestamp="2026-04-01T12:00:00Z"):
    return {
        "timestamp": timestamp,
        "level": level,
        "source": source,
        "message": "Тестовое сообщение",
    }


def write_jsonl(path, events):
    with open(path, "w", encoding="utf-8") as file:
        file.writelines(json.dumps(item, ensure_ascii=False) + "\n" for item in events)


def write_csv(path, events):
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=["timestamp", "level", "source", "message"]
        )
        writer.writeheader()
        writer.writerows(events)


@pytest.mark.parametrize("file_format", ["csv", "jsonl"])
def test_empty_file(tmp_path, file_format):
    path = tmp_path / ("empty." + file_format)
    path.write_text("", encoding="utf-8")

    result = analyze_files([str(path)], file_format)

    assert result["total_events"] == 0
    assert result["first_timestamp"] is None
    assert result["last_timestamp"] is None
    assert result["top_error_sources"] == []
    assert result["skipped_invalid"] == 0
    assert all(value == 0 for value in result["by_level"].values())


def test_same_stats_csv_jsonl(tmp_path):
    events = [event(), event("ERROR", "база"), event("CRITICAL", "база")]
    csv_path = tmp_path / "a.csv"
    jsonl_path = tmp_path / "a.jsonl"
    write_csv(csv_path, events)
    write_jsonl(jsonl_path, events)

    csv_result = analyze_files([str(csv_path)], "csv")
    jsonl_result = analyze_files([str(jsonl_path)], "jsonl")

    assert csv_result == jsonl_result


def test_multiple_files(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    write_jsonl(first, [event(), event("ERROR", "база")])
    write_jsonl(second, [event("CRITICAL", "база"), event("DEBUG", "сайт")])

    result = analyze_files([str(first), str(second)], "jsonl")

    assert result["total_events"] == 4
    assert result["by_source"] == {"сайт": 2, "база": 2}
    assert result["top_error_sources"] == [{"source": "база", "count": 2}]


def test_bad_json_line_seven(tmp_path):
    path = tmp_path / "bad.jsonl"
    good = json.dumps(event(), ensure_ascii=False)
    path.write_text((good + "\n") * 6 + "{неверный json\n" + good + "\n", encoding="utf-8")

    with pytest.raises(InvalidEventError, match="строка 7"):
        analyze_files([str(path)], "jsonl")


def test_skip_bad_json(tmp_path, caplog):
    path = tmp_path / "bad.jsonl"
    good = json.dumps(event(), ensure_ascii=False)
    path.write_text(good + "\n{неверный json\n" + good + "\n", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        result = analyze_files([str(path)], "jsonl", skip_invalid=True)

    assert result["total_events"] == 2
    assert result["skipped_invalid"] == 1
    assert "строка 2" in caplog.text
    assert "WARNING" in caplog.text


def test_bad_csv_both_modes(tmp_path, caplog):
    path = tmp_path / "bad.csv"
    write_csv(path, [event(), event(source=""), event("ERROR", "база")])

    with pytest.raises(InvalidEventError, match="строка 3"):
        analyze_files([str(path)], "csv")

    with caplog.at_level(logging.WARNING):
        result = analyze_files([str(path)], "csv", skip_invalid=True)

    assert result["total_events"] == 2
    assert result["skipped_invalid"] == 1
    assert result["by_level"]["ERROR"] == 1
    assert "строка 3" in caplog.text


def test_wrong_timestamp_shows_line(tmp_path):
    path = tmp_path / "wrong.jsonl"
    write_jsonl(path, [event(timestamp="2026-02-30T12:00:00Z")])

    with pytest.raises(InvalidTimestampError, match="строка 1: поле timestamp"):
        analyze_files([str(path)], "jsonl")


def test_top_five_tie_break(tmp_path):
    path = tmp_path / "errors.jsonl"
    events = [event("ERROR", source) for source in ["ж", "б", "г", "а", "в", "д"]]
    write_jsonl(path, events)

    result = analyze_files([str(path)], "jsonl")
    names = [item["source"] for item in result["top_error_sources"]]

    assert names == ["а", "б", "в", "г", "д"]


def test_top_n(tmp_path):
    path = tmp_path / "errors.jsonl"
    write_jsonl(path, [event("ERROR", name) for name in ["а", "б", "в"]])

    result = analyze_files([str(path)], "jsonl", top_n=2)

    assert len(result["top_error_sources"]) == 2


def test_first_last_timestamp(tmp_path):
    path = tmp_path / "times.jsonl"
    write_jsonl(path, [
        event(timestamp="2026-04-01T14:00:00+02:00"),
        event(timestamp="2026-04-01T10:00:00Z"),
        event(timestamp="2026-04-01T15:00:00Z"),
    ])

    result = analyze_files([str(path)], "jsonl")

    assert result["first_timestamp"] == "2026-04-01T10:00:00Z"
    assert result["last_timestamp"] == "2026-04-01T15:00:00Z"


def test_wrong_format():
    with pytest.raises(UnsupportedFormatError):
        analyze_files([], "txt")


def test_wrong_top():
    with pytest.raises(CLIConfigError):
        analyze_files([], "jsonl", top_n=0)