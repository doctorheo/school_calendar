import argparse
from pathlib import Path

import requests


DEFAULT_URL = "https://bunwon-e.goegh.kr/bunwon-e/ps/schdul/selectSchdulMainList.do?mi=2547"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "output" / "school_schedule.html"


def fetch_website(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


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
