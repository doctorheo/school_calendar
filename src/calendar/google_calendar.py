from __future__ import annotations

import argparse
import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

from src.calendar.merge_events import merge_events


SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TIMEZONE = "Asia/Seoul"
DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "parse" / "output" / "parsed_schedule.json"


def _parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is required.")
    return value


def _build_service(credentials_path: str):
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar dependencies are missing. "
            "Install 'google-api-python-client' and 'google-auth'."
        ) from exc

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials)


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    return value or None


def _make_event_key(title: str, start_date: str, end_date: str) -> str:
    raw = f"{title}|{start_date}|{end_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _find_existing_event(service, calendar_id: str, event_key: str):
    response = (
        service.events()
        .list(
            calendarId=calendar_id,
            privateExtendedProperty=f"schoolCalendarKey={event_key}",
            singleEvents=True,
            maxResults=1,
        )
        .execute()
    )
    items = response.get("items", [])
    return items[0] if items else None


def _to_google_event(schedule: dict[str, str], timezone: str) -> dict:
    start_date = _parse_date(schedule["start_date"])
    end_date = _parse_date(schedule["end_date"])

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    # Google Calendar all-day events use an exclusive end date.
    exclusive_end = end_date + timedelta(days=1)
    event_key = _make_event_key(
        schedule["title"],
        start_date.isoformat(),
        end_date.isoformat(),
    )

    return {
        "summary": schedule["title"],
        "description": "Imported by school_calendar",
        "start": {
            "date": start_date.isoformat(),
            "timeZone": timezone,
        },
        "end": {
            "date": exclusive_end.isoformat(),
            "timeZone": timezone,
        },
        "extendedProperties": {
            "private": {
                "schoolCalendarKey": event_key,
            }
        },
    }


def create_calendar(
    *,
    summary: str,
    credentials_path: str | None = None,
    timezone: str = DEFAULT_TIMEZONE,
    description: str | None = None,
) -> dict[str, str]:
    if not summary.strip():
        raise ValueError("Calendar summary is required.")

    credentials_path = credentials_path or _get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE")
    service = _build_service(credentials_path)
    body = {
        "summary": summary.strip(),
        "timeZone": timezone,
    }
    if description:
        body["description"] = description

    created = service.calendars().insert(body=body).execute()
    return {
        "id": created["id"],
        "summary": created.get("summary", summary.strip()),
        "timeZone": created.get("timeZone", timezone),
    }


def create_calendar_events(
    schedules: Iterable[dict[str, str]],
    *,
    calendar_id: str | None = None,
    credentials_path: str | None = None,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[dict[str, str]]:
    calendar_id = calendar_id or _get_required_env("GOOGLE_CALENDAR_ID")
    credentials_path = credentials_path or _get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE")

    merged_schedules = merge_events(list(schedules))
    service = _build_service(credentials_path)
    results: list[dict[str, str]] = []

    for schedule in merged_schedules:
        event_body = _to_google_event(schedule, timezone)
        event_key = event_body["extendedProperties"]["private"]["schoolCalendarKey"]
        existing = _find_existing_event(service, calendar_id, event_key)

        if existing:
            results.append(
                {
                    "title": schedule["title"],
                    "start_date": schedule["start_date"],
                    "end_date": schedule["end_date"],
                    "status": "skipped",
                    "google_event_id": existing["id"],
                }
            )
            continue

        created = (
            service.events()
            .insert(calendarId=calendar_id, body=event_body)
            .execute()
        )
        results.append(
            {
                "title": schedule["title"],
                "start_date": schedule["start_date"],
                "end_date": schedule["end_date"],
                "status": "created",
                "google_event_id": created["id"],
            }
        )

    return results


def create_calendar_and_events(
    schedules: Iterable[dict[str, str]],
    *,
    calendar_summary: str | None,
    credentials_path: str | None = None,
    timezone: str = DEFAULT_TIMEZONE,
    description: str | None = None,
) -> dict[str, object]:
    calendar_summary = calendar_summary or _get_optional_env("GOOGLE_CALENDAR_NAME")
    if not calendar_summary:
        raise RuntimeError(
            "Calendar name is required when creating a calendar. "
            "Pass --calendar-name or set GOOGLE_CALENDAR_NAME."
        )

    created_calendar = create_calendar(
        summary=calendar_summary,
        credentials_path=credentials_path,
        timezone=timezone,
        description=description,
    )
    results = create_calendar_events(
        schedules,
        calendar_id=created_calendar["id"],
        credentials_path=credentials_path,
        timezone=timezone,
    )
    return {
        "calendar": created_calendar,
        "events": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Google Calendar events from parsed schedules.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to parsed schedule JSON.",
    )
    parser.add_argument(
        "--calendar-id",
        default=None,
        help="Google Calendar ID. Defaults to GOOGLE_CALENDAR_ID from .env or environment.",
    )
    parser.add_argument(
        "--create-calendar",
        action="store_true",
        help="Create a new Google Calendar before inserting events.",
    )
    parser.add_argument(
        "--calendar-name",
        default=None,
        help="New calendar name. Defaults to GOOGLE_CALENDAR_NAME from .env or environment.",
    )
    parser.add_argument(
        "--calendar-description",
        default=None,
        help="Optional description for a new calendar.",
    )
    parser.add_argument(
        "--credentials-path",
        default=None,
        help="Path to service account JSON. Defaults to GOOGLE_SERVICE_ACCOUNT_FILE from .env or environment.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help="Timezone for all-day events.",
    )
    args = parser.parse_args()

    load_dotenv()

    if args.create_calendar and args.calendar_id:
        raise RuntimeError("Use either --calendar-id or --create-calendar, not both.")

    input_path = Path(args.input)
    schedules = json.loads(input_path.read_text(encoding="utf-8"))
    calendar_name = args.calendar_name or _get_optional_env("GOOGLE_CALENDAR_NAME")

    if args.create_calendar:
        results = create_calendar_and_events(
            schedules,
            calendar_summary=calendar_name,
            credentials_path=args.credentials_path,
            timezone=args.timezone,
            description=args.calendar_description,
        )
    else:
        results = create_calendar_events(
            schedules,
            calendar_id=args.calendar_id,
            credentials_path=args.credentials_path,
            timezone=args.timezone,
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    if isinstance(results, dict):
        print(len(results["events"]))
    else:
        print(len(results))


if __name__ == "__main__":
    # uv run python -m src.calendar.google_calendar
    main()
