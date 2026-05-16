import json
import re
from html import unescape
from pathlib import Path

from loguru import logger
import yaml


DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "fetch" / "output" / "school_schedule.html"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "parsed_schedule.json"
DEFAULT_CONFIG_PATH = Path("src/config/parse_schedule.yml")


def parse_schedule(html: str):
    logger.info("parsing school schedule html")
    table_html = unescape(html)
    matches = re.finditer(
        r"href=\"javascript:viewSchdulInfo\(\s*'(?P<seq>[^']*)'\s*,\s*'(?P<start>[^']*)'\s*,\s*'(?P<end>[^']*)'\s*,\s*'[^']*'\s*\);\"\s*>\s*(?P<title>.*?)</a>",
        table_html,
        re.S,
    )

    schedules = []
    for match in matches:
        title = re.sub(r"\s+", " ", unescape(match.group("title"))).strip()
        if not title:
            continue
        schedules.append(
            {
                "title": title,
                "start_date": match.group("start").replace("/", "-"),
                "end_date": match.group("end").replace("/", "-"),
            }
        )

    logger.info("parsed {} schedule entries", len(schedules))
    return schedules


def save_schedule(schedules, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    logger.info("saving {} schedules to {}", len(schedules), output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(schedules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("saved parsed schedules to {}", output_path)
    return output_path


def load_parse_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> tuple[Path, Path]:
    config_path = Path(config_path)
    logger.info("loading parse config from {}", config_path)
    if not config_path.exists():
        raise RuntimeError(f"Parse config file not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise RuntimeError("Parse config file root must be a YAML mapping.")

    schedule = data.get("schedule", {})
    if not isinstance(schedule, dict):
        raise RuntimeError("'schedule' section must be a YAML mapping.")

    input_value = schedule.get("html_input")
    output_value = schedule.get("parsed_output")

    if input_value is None:
        input_path = DEFAULT_INPUT_PATH
    elif isinstance(input_value, str) and input_value.strip():
        input_path = Path(input_value.strip())
    else:
        raise RuntimeError("'schedule.html_input' must be a non-empty string.")

    if output_value is None:
        output_path = DEFAULT_OUTPUT_PATH
    elif isinstance(output_value, str) and output_value.strip():
        output_path = Path(output_value.strip())
    else:
        raise RuntimeError("'schedule.parsed_output' must be a non-empty string.")

    logger.info("parse config loaded: html_input={}, parsed_output={}", input_path, output_path)
    return input_path, output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse school schedule HTML into JSON.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    input_path, output_path = load_parse_config(args.config)
    html = input_path.read_text(encoding="utf-8")
    schedules = parse_schedule(html)
    output_path = save_schedule(schedules, output_path)
    print(len(schedules))
    print(output_path)
