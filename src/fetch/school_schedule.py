import argparse
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger


DEFAULT_URL = "https://bunwon-e.goegh.kr/bunwon-e/ps/schdul/selectSchdulMainList.do?mi=2547"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "school_schedule.html"


def _build_schedule_list_url(url: str) -> tuple[str, dict[str, str]]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    menu_id = query.get("mi", [""])[0]
    if not menu_id:
        raise RuntimeError("School schedule URL must include the 'mi' query parameter.")

    schedule_path = parsed.path.replace(
        "/selectSchdulMainList.do",
        "/selectSchdulList.do",
    )
    schedule_url = parsed._replace(path=schedule_path).geturl()
    payload = {
        "schdulSeq": "",
        "schdulLevel": "Y",
        "fromDate": "",
        "toDate": "",
        "date": "",
        "weekNum": "",
        "chkNP": "",
        "srchDate": "",
        "schType": "",
        "schColor": "",
        "menuId": menu_id,
    }
    return schedule_url, payload


def fetch_website(url: str) -> str:
    logger.info("fetching school schedule from {}", url)
    schedule_url, payload = _build_schedule_list_url(url)
    response = requests.post(
        schedule_url,
        data=payload,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    html = response.json()
    logger.info(
        "fetched school schedule successfully: status_code={}, response_length={}",
        response.status_code,
        len(html),
    )
    return html


def main():
    parser = argparse.ArgumentParser(description="Fetch school schedule page HTML.")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Target school schedule URL.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to save fetched HTML.",
    )
    args = parser.parse_args()

    html = fetch_website(args.url)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    # uv run python -m src.fetch.school_schedule
    main()
