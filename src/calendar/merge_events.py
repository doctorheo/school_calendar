from __future__ import annotations

import json
from pprint import pprint
from datetime import date, datetime, timedelta
from pathlib import Path


DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "parse" / "output" / "parsed_schedule.json"


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
        return []

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
    return merged_events


def main() -> None:
    events = json.loads(DEFAULT_INPUT_PATH.read_text(encoding="utf-8"))
    pprint(merge_events(events))


if __name__ == "__main__":
    # uv run python -m src.calendar.merge_events
    main()
