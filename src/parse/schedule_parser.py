import json
import re
from html import unescape
from pathlib import Path


DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "fetch" / "output" / "school_schedule.html"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "parsed_schedule.json"


def parse_schedule(html: str):
    table_html = unescape(html)
    matches = re.finditer(
        r"viewSchdulInfo\('(?P<seq>[^']*)',\s*'(?P<start>[^']*)',\s*'(?P<end>[^']*)',\s*'[^']*'\);\">(?P<title>.*?)</a>",
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

    return schedules


def save_schedule(schedules, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(schedules, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    # uv run python -m src.parse.schedule_parser
    html = DEFAULT_INPUT_PATH.read_text(encoding="utf-8")
    schedules = parse_schedule(html)
    output_path = save_schedule(schedules)
    print(len(schedules))
    print(output_path)
