import json
from pathlib import Path

from dotenv import load_dotenv

from src.config.app_config import DEFAULT_CONFIG_PATH, load_app_config
from src.fetch.school_schedule import fetch_website
from src.parse.schedule_parser import parse_schedule, save_schedule
from src.calendar.google_calendar import create_calendar_and_events, create_calendar_events


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fetch school schedules and create Google Calendar events.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    load_dotenv()
    config = load_app_config(Path(args.config))
    html = fetch_website(config.url)
    schedules = parse_schedule(html)
    if config.parsed_output:
        save_schedule(schedules, config.parsed_output)

    if config.create_calendar:
        results = create_calendar_and_events(
            schedules,
            calendar_summary=config.calendar_name,
            credentials_path=config.credentials_path,
            timezone=config.timezone,
            description=config.calendar_description,
        )
    else:
        results = create_calendar_events(
            schedules,
            calendar_id=config.calendar_id,
            credentials_path=config.credentials_path,
            timezone=config.timezone,
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    if isinstance(results, dict):
        print(len(results["events"]))
    else:
        print(len(results))


if __name__ == "__main__":
    # uv run python -m src.main
    main()
