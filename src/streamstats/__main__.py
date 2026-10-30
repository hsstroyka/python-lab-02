import argparse
import csv
import logging
import os
import sys

from .analysis import analyze_files
from .errors import CLIConfigError, StreamStatsError
from .report import report_to_json, save_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Анализ событий CSV и JSONL")
    commands = parser.add_subparsers(dest="command")

    analyze = commands.add_parser("analyze", help="анализировать файлы")
    analyze.add_argument("inputs", nargs="+", help="входные файлы")
    analyze.add_argument("--format", choices=["csv", "jsonl"], required=True)
    analyze.add_argument("--output", help="имя JSON-отчёта")
    analyze.add_argument("--skip-invalid", action="store_true")
    analyze.add_argument("--top", type=int, default=5)

    args = parser.parse_args()

    if args.command != "analyze":
        parser.print_help()
        return 0

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    try:
        if args.top < 1:
            raise CLIConfigError("число для --top должно быть больше нуля")

        if args.output:
            for filename in args.inputs:
                if os.path.abspath(filename) == os.path.abspath(args.output):
                    raise CLIConfigError("нельзя перезаписывать входной файл")

        result = analyze_files(args.inputs, args.format, args.skip_invalid, args.top)

        if args.output:
            save_report(result, args.output)
        else:
            print(report_to_json(result))

    except (StreamStatsError, OSError, UnicodeError, csv.Error) as error:
        print("Ошибка:", error, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())