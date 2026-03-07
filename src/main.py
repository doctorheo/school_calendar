from src.fetch.school_schedule import fetch_website
from src.parse.schedule_parser import parse_schedule
from src.calendar.google_calendar import create_calendar_events


URL = "https://bunwon-e.goegh.kr/bunwon-e/ps/schdul/selectSchdulMainList.do?mi=2547"


def main():
    html = fetch_website(URL)
    schedules = parse_schedule(html)
    create_calendar_events(schedules)


if __name__ == "__main__":
    main()
