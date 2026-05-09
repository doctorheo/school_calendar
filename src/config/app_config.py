from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from loguru import logger

from src.calendar.google_calendar import DEFAULT_TIMEZONE
from src.fetch.school_schedule import DEFAULT_URL


DEFAULT_CONFIG_PATH = Path("src/config/school_calendar.yml")
SHARE_WITH_EMAIL_ENV = "GOOGLE_CALENDAR_SHARE_WITH_EMAIL"


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
    share_with_email: str | None = None
    share_role: str = "reader"


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


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


def _get_bool(data: dict, key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise RuntimeError(f"'{key}' must be a boolean in the config file.")
    return value


def load_app_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(config_path)
    logger.info("loading application config from {}", config_path)
    if not config_path.exists():
        raise RuntimeError(
            f"Config file not found: {config_path}. "
            "Create one from 'src/config/school_calendar.yml'."
        )

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise RuntimeError("Config file root must be a YAML mapping.")

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
    share_with_email = _get_optional_string(calendar, "share_with_email") or _get_optional_env(
        SHARE_WITH_EMAIL_ENV
    )
    share_role = _get_optional_string(calendar, "share_role") or "reader"

    valid_share_roles = {"reader", "writer", "owner", "freeBusyReader"}
    if share_role not in valid_share_roles:
        raise RuntimeError(
            f"'calendar.share_role' must be one of {sorted(valid_share_roles)}."
        )

    if create_calendar and calendar_id:
        raise RuntimeError("Use either 'calendar.create: true' or 'calendar.id', not both.")
    if create_calendar and not calendar_name:
        raise RuntimeError("'calendar.name' is required when 'calendar.create = true'.")
    if not create_calendar and not calendar_id:
        raise RuntimeError("'calendar.id' is required unless 'calendar.create = true'.")

    config = AppConfig(
        url=url,
        parsed_output=parsed_output,
        calendar_id=calendar_id,
        create_calendar=create_calendar,
        calendar_name=calendar_name,
        calendar_description=calendar_description,
        timezone=timezone,
        credentials_path=credentials_path,
        share_with_email=share_with_email,
        share_role=share_role,
    )
    logger.info(
        "application config validated: create_calendar={}, calendar_id={}, calendar_name={}, share_with_email={}, share_role={}",
        config.create_calendar,
        config.calendar_id,
        config.calendar_name,
        config.share_with_email,
        config.share_role,
    )
    return config
