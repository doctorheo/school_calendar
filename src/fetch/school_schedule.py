import requests


def fetch_website(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


if __name__ == "__main__":
    url = "https://bunwon-e.goegh.kr/bunwon-e/ps/schdul/selectSchdulMainList.do?mi=2547"
    html = fetch_website(url)
    print(html)
