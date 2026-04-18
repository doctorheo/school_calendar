from __future__ import annotations

import argparse
import json
from pprint import pprint
from datetime import date, datetime, timedelta
from pathlib import Path

from loguru import logger
import yaml


DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "parse" / "output" / "parsed_schedule.json"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "parse" / "output" / "merged_events.json"
DEFAULT_CONFIG_PATH = Path("src/config/merge_events.yml")


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _to_event(title: str, start_date: date, end_date: date) -> dict[str, str]:
    return {
        "title": title,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def merge_events(events: list[dict[str, str]]) -> list[dict[str, str]]:
    if not events:
        logger.info("merge_events received no events")
        return []

    logger.info("merging {} events by title and date range", len(events))
    grouped_events: dict[str, list[tuple[date, date]]] = {}

    for event in events:
        title = event["title"].strip()
        start_date = _parse_date(event["start_date"])
        end_date = _parse_date(event["end_date"])

        if end_date < start_date:
            start_date, end_date = end_date, start_date

        grouped_events.setdefault(title, []).append((start_date, end_date))

    merged_events: list[dict[str, str]] = []

    for title, ranges in grouped_events.items():
        if not ranges:
            continue

        ranges.sort()
        current_start, current_end = ranges[0]

        for next_start, next_end in ranges[1:]:
            if next_start <= current_end + timedelta(days=1):
                current_end = max(current_end, next_end)
                continue

            merged_events.append(_to_event(title, current_start, current_end))
            current_start, current_end = next_start, next_end

        merged_events.append(_to_event(title, current_start, current_end))

    merged_events.sort(key=lambda event: (event["start_date"], event["end_date"], event["title"]))
    logger.info("merged events down to {} entries", len(merged_events))
    return merged_events


def save_merged_events(
    events: list[dict[str, str]],
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    logger.info("saving {} merged events to {}", len(events), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("saved merged events to {}", output_path)
    return output_path


def load_merge_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> tuple[Path, Path]:
    config_path = Path(config_path)
    logger.info("loading merge config from {}", config_path)
    if not config_path.exists():
        raise RuntimeError(f"Merge config file not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise RuntimeError("Merge config file root must be a YAML mapping.")

    schedule = data.get("schedule", {})
    if not isinstance(schedule, dict):
        raise RuntimeError("'schedule' section must be a YAML mapping.")

    input_value = schedule.get("parsed_input")
    output_value = schedule.get("merged_output")

    if input_value is None:
        input_path = DEFAULT_INPUT_PATH
    elif isinstance(input_value, str) and input_value.strip():
        input_path = Path(input_value.strip())
    else:
        raise RuntimeError("'schedule.parsed_input' must be a non-empty string.")

    if output_value is None:
        output_path = DEFAULT_OUTPUT_PATH
    elif isinstance(output_value, str) and output_value.strip():
        output_path = Path(output_value.strip())
    else:
        raise RuntimeError("'schedule.merged_output' must be a non-empty string.")

    logger.info("merge config loaded: parsed_input={}, merged_output={}", input_path, output_path)
    return input_path, output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge parsed school schedule events.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    input_path, output_path = load_merge_config(args.config)
    events = json.loads(input_path.read_text(encoding="utf-8"))
    merged_events = merge_events(events)
    output_path = save_merged_events(merged_events, output_path)
    pprint(merged_events)
    print(output_path)


if __name__ == "__main__":
    # uv run python -m src.calendar.merge_events
    main()
