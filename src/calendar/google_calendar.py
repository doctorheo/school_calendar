from __future__ import annotations

import argparse
import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from loguru import logger

from src.calendar.merge_events import merge_events
from src.logging_config import configure_logging


SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TIMEZONE = "Asia/Seoul"
DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "parse" / "output" / "parsed_schedule.json"
DEFAULT_SHARE_ROLE = "reader"


def _parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable '{name}' is required.")
    return value


def _build_service(credentials_path: str):
    logger.info("building Google Calendar service using credentials_path={}", credentials_path)
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
    logger.info("Google Calendar service authenticated successfully")
    return build("calendar", "v3", credentials=credentials)


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    return value or None


def _make_event_key(title: str, start_date: str, end_date: str) -> str:
    raw = f"{title}|{start_date}|{end_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _find_existing_event(service, calendar_id: str, event_key: str):
    logger.debug("checking existing event for calendar_id={} event_key={}", calendar_id, event_key)
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
    if items:
        logger.info("found existing event for event_key={} in calendar_id={}", event_key, calendar_id)
    return items[0] if items else None


def _find_acl_rule(service, calendar_id: str, email: str):
    response = service.acl().list(calendarId=calendar_id, showDeleted=False).execute()
    for item in response.get("items", []):
        scope = item.get("scope", {})
        if scope.get("type") == "user" and scope.get("value") == email:
            return item
    return None


def ensure_calendar_access(
    calendar_id: str,
    *,
    share_with_email: str | None,
    role: str = DEFAULT_SHARE_ROLE,
    credentials_path: str | None = None,
) -> dict[str, str] | None:
    if not share_with_email:
        logger.debug("calendar sharing skipped because no share_with_email was provided")
        return None

    credentials_path = credentials_path or _get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE")
    logger.info(
        "ensuring calendar access for email={} calendar_id={} role={}",
        share_with_email,
        calendar_id,
        role,
    )
    service = _build_service(credentials_path)
    existing_rule = _find_acl_rule(service, calendar_id, share_with_email)
    body = {
        "scope": {
            "type": "user",
            "value": share_with_email,
        },
        "role": role,
    }

    if existing_rule:
        if existing_rule.get("role") == role:
            logger.info(
                "calendar access already exists for email={} with role={}",
                share_with_email,
                role,
            )
            return {
                "email": share_with_email,
                "role": role,
                "status": "unchanged",
            }

        service.acl().update(
            calendarId=calendar_id,
            ruleId=existing_rule["id"],
            body=body,
            sendNotifications=False,
        ).execute()
        logger.info(
            "updated calendar access for email={} to role={}",
            share_with_email,
            role,
        )
        return {
            "email": share_with_email,
            "role": role,
            "status": "updated",
        }

    service.acl().insert(
        calendarId=calendar_id,
        body=body,
        sendNotifications=False,
    ).execute()
    logger.info(
        "granted calendar access to email={} with role={}",
        share_with_email,
        role,
    )
    return {
        "email": share_with_email,
        "role": role,
        "status": "granted",
    }


def grant_reader_access_to_user(
    calendar_id: str,
    user_email: str,
    *,
    credentials_path: str | None = None,
) -> dict[str, str]:
    if not user_email.strip():
        raise ValueError("user_email is required.")

    return ensure_calendar_access(
        calendar_id,
        share_with_email=user_email.strip(),
        role="reader",
        credentials_path=credentials_path,
    ) or {
        "email": user_email.strip(),
        "role": "reader",
        "status": "skipped",
    }


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
    logger.info("creating Google Calendar with summary={} timezone={}", summary.strip(), timezone)
    service = _build_service(credentials_path)
    body = {
        "summary": summary.strip(),
        "timeZone": timezone,
    }
    if description:
        body["description"] = description

    created = service.calendars().insert(body=body).execute()
    logger.info("created Google Calendar id={}", created["id"])
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
    share_with_email: str | None = None,
    share_role: str = DEFAULT_SHARE_ROLE,
) -> list[dict[str, str]]:
    calendar_id = calendar_id or _get_required_env("GOOGLE_CALENDAR_ID")
    credentials_path = credentials_path or _get_required_env("GOOGLE_SERVICE_ACCOUNT_FILE")

    logger.info("creating calendar events in calendar_id={}", calendar_id)
    ensure_calendar_access(
        calendar_id,
        share_with_email=share_with_email,
        role=share_role,
        credentials_path=credentials_path,
    )
    merged_schedules = merge_events(list(schedules))
    service = _build_service(credentials_path)
    results: list[dict[str, str]] = []

    for schedule in merged_schedules:
        event_body = _to_google_event(schedule, timezone)
        event_key = event_body["extendedProperties"]["private"]["schoolCalendarKey"]
        existing = _find_existing_event(service, calendar_id, event_key)

        if existing:
            logger.info(
                "skipping existing event title={} start_date={} end_date={}",
                schedule["title"],
                schedule["start_date"],
                schedule["end_date"],
            )
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
        logger.info(
            "created event title={} start_date={} end_date={} google_event_id={}",
            schedule["title"],
            schedule["start_date"],
            schedule["end_date"],
            created["id"],
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

    logger.info("finished processing {} calendar events", len(results))
    return results


def create_calendar_and_events(
    schedules: Iterable[dict[str, str]],
    *,
    calendar_summary: str | None,
    credentials_path: str | None = None,
    timezone: str = DEFAULT_TIMEZONE,
    description: str | None = None,
    share_with_email: str | None = None,
    share_role: str = DEFAULT_SHARE_ROLE,
) -> dict[str, object]:
    calendar_summary = calendar_summary or _get_optional_env("GOOGLE_CALENDAR_NAME")
    if not calendar_summary:
        raise RuntimeError(
            "Calendar name is required when creating a calendar. "
            "Pass --calendar-name or set GOOGLE_CALENDAR_NAME."
        )

    logger.info("creating calendar and events with calendar_summary={}", calendar_summary)
    created_calendar = create_calendar(
        summary=calendar_summary,
        credentials_path=credentials_path,
        timezone=timezone,
        description=description,
    )
    sharing_result = ensure_calendar_access(
        created_calendar["id"],
        share_with_email=share_with_email,
        role=share_role,
        credentials_path=credentials_path,
    )
    results = create_calendar_events(
        schedules,
        calendar_id=created_calendar["id"],
        credentials_path=credentials_path,
        timezone=timezone,
        share_with_email=None,
        share_role=share_role,
    )
    payload = {
        "calendar": created_calendar,
        "events": results,
    }
    if sharing_result:
        payload["sharing"] = sharing_result
    return payload


def main() -> None:
    from src.config.app_config import DEFAULT_CONFIG_PATH, load_app_config

    parser = argparse.ArgumentParser(description="Create Google Calendar events from parsed schedules.")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config file used for calendar settings.",
    )
    parser.add_argument(
        "--grant-reader-access",
        action="store_true",
        help="Grant reader access using the target email from --grant-reader-email or the YAML config.",
    )
    parser.add_argument(
        "--grant-reader-email",
        default=None,
        help="Grant reader access for the given email. If omitted, uses calendar.share_with_email from YAML config.",
    )
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

    configure_logging()
    load_dotenv()
    config_path = Path(args.config) if args.config else None
    app_config = load_app_config(config_path or DEFAULT_CONFIG_PATH) if config_path else None

    if args.create_calendar and args.calendar_id:
        raise RuntimeError("Use either --calendar-id or --create-calendar, not both.")
    if args.grant_reader_email and args.create_calendar:
        raise RuntimeError("Use either --grant-reader-email or --create-calendar, not both.")
    if args.grant_reader_access and args.create_calendar:
        raise RuntimeError("Use either --grant-reader-access or --create-calendar, not both.")

    if args.grant_reader_access or args.grant_reader_email:
        calendar_id = (
            args.calendar_id
            or (app_config.calendar_id if app_config else None)
            or _get_required_env("GOOGLE_CALENDAR_ID")
        )
        share_with_email = args.grant_reader_email or (app_config.share_with_email if app_config else None)
        credentials_path = args.credentials_path or (app_config.credentials_path if app_config else None)

        result = grant_reader_access_to_user(
            calendar_id,
            share_with_email or "",
            credentials_path=credentials_path,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

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
