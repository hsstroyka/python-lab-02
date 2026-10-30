import json


def report_to_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=4)


def save_report(report: dict, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        file.write(report_to_json(report))
        file.write("\n")