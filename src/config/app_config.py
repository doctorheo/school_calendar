from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from src.calendar.google_calendar import DEFAULT_TIMEZONE
from src.fetch.school_schedule import DEFAULT_URL


DEFAULT_CONFIG_PATH = Path("school_calendar.toml")


@dataclass(frozen=True)
class AppConfig:
    url: str = DEFAULT_URL
    parsed_output: Path | None = None
    calendar_id: str | None = None
    create_calendar: bool = False
    calendar_name: str | None = None
    calendar_description: str | None = None
    timezone: str = DEFAULT_TIMEZONE
    credentials_path: str | None = None


def _get_table(data: dict, key: str) -> dict:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise RuntimeError(f"'{key}' section must be a table in the config file.")
    return value


def _get_optional_string(data: dict, key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(f"'{key}' must be a string in the config file.")

    stripped = value.strip()
    return stripped or None


def _get_bool(data: dict, key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise RuntimeError(f"'{key}' must be a boolean in the config file.")
    return value


def load_app_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(config_path)
    if not config_path.exists():
        raise RuntimeError(
            f"Config file not found: {config_path}. "
            "Create one from 'school_calendar.example.toml'."
        )

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Config file root must be a TOML table.")

    schedule = _get_table(data, "schedule")
    calendar = _get_table(data, "calendar")

    url = _get_optional_string(schedule, "url") or DEFAULT_URL
    parsed_output_value = _get_optional_string(schedule, "parsed_output")
    parsed_output = Path(parsed_output_value) if parsed_output_value else None

    create_calendar = _get_bool(calendar, "create", default=False)
    calendar_id = _get_optional_string(calendar, "id")
    calendar_name = _get_optional_string(calendar, "name")
    calendar_description = _get_optional_string(calendar, "description")
    timezone = _get_optional_string(calendar, "timezone") or DEFAULT_TIMEZONE
    credentials_path = _get_optional_string(calendar, "credentials_path")

    if create_calendar and calendar_id:
        raise RuntimeError("Use either 'calendar.create = true' or 'calendar.id', not both.")
    if create_calendar and not calendar_name:
        raise RuntimeError("'calendar.name' is required when 'calendar.create = true'.")
    if not create_calendar and not calendar_id:
        raise RuntimeError("'calendar.id' is required unless 'calendar.create = true'.")

    return AppConfig(
        url=url,
        parsed_output=parsed_output,
        calendar_id=calendar_id,
        create_calendar=create_calendar,
        calendar_name=calendar_name,
        calendar_description=calendar_description,
        timezone=timezone,
        credentials_path=credentials_path,
    )
