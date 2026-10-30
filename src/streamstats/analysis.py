import logging

from .errors import CLIConfigError, InvalidEventError, UnsupportedFormatError
from .models import LEVELS, parse_timestamp
from .parsers import parse_csv, parse_jsonl, read_csv, read_jsonl


def sort_error(item: tuple) -> tuple:
    source, count = item
    return -count, source


def analyze_files(
    filenames: list,
    file_format: str,
    skip_invalid: bool = False,
    top_n: int = 5,
) -> dict:
    if file_format not in ["csv", "jsonl"]:
        raise UnsupportedFormatError("поддерживаются только csv и jsonl")

    if top_n < 1:
        raise CLIConfigError("число для --top должно быть больше нуля")

    total = 0
    skipped = 0
    levels = {}
    sources = {}
    error_sources = {}

    for level in LEVELS:
        levels[level] = 0

    first_date = None
    last_date = None
    first_timestamp = None
    last_timestamp = None

    for file_number, filename in enumerate(filenames, 1):
        if file_format == "csv":
            rows = read_csv(filename)
            parser = parse_csv
        else:
            rows = read_jsonl(filename)
            parser = parse_jsonl

        for line_number, row in rows:
            try:
                event = parser(row)
            except InvalidEventError as error:
                message = (
                    f"файл {file_number} ({filename}), "
                    f"строка {line_number}: {error}"
                )

                if skip_invalid:
                    skipped += 1
                    logging.warning(message)
                    continue

                raise type(error)(message) from None

            total += 1
            level = event["level"]
            source = event["source"]

            levels[level] += 1

            if source not in sources:
                sources[source] = 0
            sources[source] += 1

            if level == "ERROR" or level == "CRITICAL":
                if source not in error_sources:
                    error_sources[source] = 0
                error_sources[source] += 1

            date = parse_timestamp(event["timestamp"])

            if first_date is None or date < first_date:
                first_date = date
                first_timestamp = event["timestamp"]

            if last_date is None or date > last_date:
                last_date = date
                last_timestamp = event["timestamp"]

    sorted_errors = sorted(error_sources.items(), key=sort_error)
    top_errors = []

    for source, count in sorted_errors[:top_n]:
        top_errors.append({"source": source, "count": count})

    return {
        "total_events": total,
        "by_level": levels,
        "by_source": sources,
        "top_error_sources": top_errors,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "skipped_invalid": skipped,
    }