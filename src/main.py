import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from src.fetch.school_schedule import DEFAULT_URL, fetch_website
from src.parse.schedule_parser import parse_schedule, save_schedule
from src.calendar.google_calendar import create_calendar_and_events, create_calendar_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch school schedules and create Google Calendar events.")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="School schedule page URL.",
    )
    parser.add_argument(
        "--parsed-output",
        default=None,
        help="Optional path to save parsed schedule JSON before calendar sync.",
    )
    parser.add_argument(
        "--calendar-id",
        default=None,
        help="Existing Google Calendar ID. Defaults to GOOGLE_CALENDAR_ID from .env or environment.",
    )
    parser.add_argument(
        "--create-calendar",
        action="store_true",
        help="Create a new Google Calendar before syncing events.",
    )
    parser.add_argument(
        "--calendar-name",
        default=None,
        help="New calendar name. Required with --create-calendar unless GOOGLE_CALENDAR_NAME is set.",
    )
    parser.add_argument(
        "--calendar-description",
        default=None,
        help="Optional description for the new calendar.",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Seoul",
        help="Timezone for Google Calendar and all-day events.",
    )
    parser.add_argument(
        "--credentials-path",
        default=None,
        help="Path to service account JSON. Defaults to GOOGLE_SERVICE_ACCOUNT_FILE from .env or environment.",
    )
    args = parser.parse_args()

    load_dotenv()
    if args.create_calendar and args.calendar_id:
        raise RuntimeError("Use either --calendar-id or --create-calendar, not both.")

    html = fetch_website(args.url)
    schedules = parse_schedule(html)
    if args.parsed_output:
        save_schedule(schedules, Path(args.parsed_output))

    if args.create_calendar:
        results = create_calendar_and_events(
            schedules,
            calendar_summary=args.calendar_name,
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
    # uv run python -m src.main
    main()
