from datetime import datetime, timezone

from .errors import InvalidEventError, InvalidTimestampError

LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
FIELDS = ["timestamp", "level", "source", "message"]


def parse_timestamp(text: str) -> datetime:
    if "T" not in text:
        raise InvalidTimestampError("поле timestamp: нужен формат ISO 8601")

    try:
        date = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise InvalidTimestampError("поле timestamp: неверная дата") from None

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return date.astimezone(timezone.utc)


def validate_event(event: dict) -> dict:
    if not isinstance(event, dict):
        raise InvalidEventError("событие должно быть словарём")

    for field in FIELDS:
        if field not in event:
            raise InvalidEventError(f"нет поля {field}")

        if not isinstance(event[field], str):
            raise InvalidEventError(f"поле {field} должно быть строкой")

    if event["level"] not in LEVELS:
        raise InvalidEventError("поле level: неизвестный уровень")

    if not event["source"].strip():
        raise InvalidEventError("поле source не должно быть пустым")

    parse_timestamp(event["timestamp"])

    return event