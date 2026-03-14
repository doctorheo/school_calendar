import json
import re
from html import unescape
from pathlib import Path

import requests


DEFAULT_INPUT_PATH = Path(__file__).resolve().parents[1] / "fetch" / "output" / "school_schedule.html"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "parsed_schedule.json"


def parse_schedule(html: str):
    sys_id_match = re.search(r'<input[^>]*id="sysId"[^>]*value="([^"]*)"', html)
    menu_id_match = re.search(r'<input[^>]*id="mi"[^>]*value="([^"]*)"', html)
    level_match = re.search(r"var schdulLevel = '([A-Z])';", html)

    if not sys_id_match or not menu_id_match:
        return []

    sys_id = sys_id_match.group(1)
    menu_id = menu_id_match.group(1)
    schedule_level = level_match.group(1) if level_match else "Y"

    response = requests.post(
        f"https://{sys_id}.goegh.kr/{sys_id}/ps/schdul/selectSchdulList.do?mi={menu_id}",
        data={
            "schdulSeq": "",
            "schdulLevel": schedule_level,
            "fromDate": "",
            "toDate": "",
            "date": "",
            "weekNum": "",
            "chkNP": "",
            "srchDate": "",
            "schType": "",
            "schColor": "",
            "menuId": menu_id,
        },
        headers={
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=10,
    )
    response.raise_for_status()

    table_html = unescape(json.loads(response.text))
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
