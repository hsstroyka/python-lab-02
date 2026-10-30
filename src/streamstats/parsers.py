import csv
import json

from .errors import InvalidEventError
from .models import validate_event


def read_csv(filename: str):
    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            yield reader.line_num, row


def read_jsonl(filename: str):
    with open(filename, "r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, 1):
            yield line_number, line


def parse_csv(row: dict) -> dict:
    if None in row:
        raise InvalidEventError("в строке CSV слишком много значений")

    return validate_event(row)


def parse_jsonl(line: str) -> dict:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        raise InvalidEventError("неверный JSON") from None

    return validate_event(event)