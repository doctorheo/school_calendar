import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from src.fetch.school_schedule import DEFAULT_URL, fetch_website
from src.parse.schedule_parser import parse_schedule, save_schedule
from src.calendar.google_calendar import create_calendar_events


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
    args = parser.parse_args()

    load_dotenv()
    html = fetch_website(args.url)
    schedules = parse_schedule(html)
    if args.parsed_output:
        save_schedule(schedules, Path(args.parsed_output))
    results = create_calendar_events(schedules)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(len(results))


if __name__ == "__main__":
    # uv run python -m src.main
    main()
