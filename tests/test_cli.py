import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cli(folder, *arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")

    return subprocess.run(
        [sys.executable, "-m", "streamstats", *arguments],
        cwd=folder,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_write_json_report(tmp_path):
    path = tmp_path / "input.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-01T10:00:00Z","level":"INFO",'
        '"source":"сайт","message":"Привет"}\n',
        encoding="utf-8",
    )

    result = run_cli(
        tmp_path, "analyze", "input.jsonl", "--format", "jsonl", "--output", "report.json"
    )

    assert result.returncode == 0
    report_text = (tmp_path / "report.json").read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["total_events"] == 1
    assert report["by_source"] == {"сайт": 1}
    assert "сайт" in report_text


def test_wrong_input_exit_two(tmp_path):
    path = tmp_path / "input.jsonl"
    path.write_text("{broken\n", encoding="utf-8")
    before = path.read_bytes()

    result = run_cli(tmp_path, "analyze", "input.jsonl", "--format", "jsonl")

    assert result.returncode == 2
    assert "строка 1" in result.stderr
    assert path.read_bytes() == before


def test_skip_invalid_cli(tmp_path):
    path = tmp_path / "input.jsonl"
    path.write_text(
        '{"timestamp":"2026-04-01T10:00:00Z","level":"INFO",'
        '"source":"сайт","message":"Привет"}\n{broken\n',
        encoding="utf-8",
    )

    result = run_cli(
        tmp_path, "analyze", "input.jsonl", "--format", "jsonl", "--skip-invalid"
    )

    assert result.returncode == 0
    assert json.loads(result.stdout)["skipped_invalid"] == 1
    assert "WARNING" in result.stderr


def test_protect_input(tmp_path):
    path = tmp_path / "input.jsonl"
    path.write_text("", encoding="utf-8")

    result = run_cli(
        tmp_path, "analyze", "input.jsonl", "--format", "jsonl", "--output", "input.jsonl"
    )

    assert result.returncode == 2
    assert path.read_text(encoding="utf-8") == ""


def test_help(tmp_path):
    result = run_cli(tmp_path, "--help")

    assert result.returncode == 0
    assert "analyze" in result.stdout


def test_bad_top(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    result = run_cli(
        tmp_path, "analyze", "empty.jsonl", "--format", "jsonl", "--top", "0"
    )

    assert result.returncode == 2
    assert "--top" in result.stderr