from __future__ import annotations

import calendar
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import streamlit as st


DEFAULT_EVENTS_PATH = Path(__file__).resolve().parents[2] / "src" / "parse" / "output" / "merged_events.json"
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


@dataclass(frozen=True)
class ScheduleEvent:
    title: str
    start_date: date
    end_date: date


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_events(path: Path = DEFAULT_EVENTS_PATH) -> tuple[list[ScheduleEvent], str | None]:
    if not path.exists():
        return [], f"병합 일정 파일을 찾을 수 없습니다: {path}"

    try:
        raw_events = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], f"병합 일정 파일의 JSON 형식이 올바르지 않습니다: {exc}"

    if not isinstance(raw_events, list):
        return [], "병합 일정 파일의 최상위 형식은 목록이어야 합니다."
    if not raw_events:
        return [], "병합 일정 파일에 표시할 일정이 없습니다."

    events: list[ScheduleEvent] = []
    for index, raw_event in enumerate(raw_events, start=1):
        if not isinstance(raw_event, dict):
            return [], f"{index}번째 일정 형식이 올바르지 않습니다."

        try:
            title = str(raw_event["title"]).strip()
            start_date = parse_date(str(raw_event["start_date"]))
            end_date = parse_date(str(raw_event["end_date"]))
        except KeyError as exc:
            return [], f"{index}번째 일정에 필요한 값이 없습니다: {exc}"
        except ValueError as exc:
            return [], f"{index}번째 일정의 날짜 형식이 올바르지 않습니다: {exc}"

        if not title:
            return [], f"{index}번째 일정의 제목이 비어 있습니다."
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        events.append(ScheduleEvent(title=title, start_date=start_date, end_date=end_date))

    events.sort(key=lambda event: (event.start_date, event.end_date, event.title))
    return events, None


def month_options(events: Iterable[ScheduleEvent]) -> tuple[list[int], int, int]:
    years = sorted({event.start_date.year for event in events} | {event.end_date.year for event in events})
    today = date.today()
    if not years:
        return [today.year], today.year, today.month

    default_year = today.year if today.year in years else years[0]
    return years, default_year, today.month


def overlaps_month(event: ScheduleEvent, year: int, month: int) -> bool:
    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    return event.start_date <= month_end and event.end_date >= month_start


def dates_in_month(event: ScheduleEvent, year: int, month: int) -> Iterable[date]:
    _, last_day = calendar.monthrange(year, month)
    current = max(event.start_date, date(year, month, 1))
    end = min(event.end_date, date(year, month, last_day))

    while current <= end:
        yield current
        current += timedelta(days=1)


def events_by_day(events: Iterable[ScheduleEvent], year: int, month: int) -> dict[date, list[ScheduleEvent]]:
    grouped: dict[date, list[ScheduleEvent]] = defaultdict(list)
    for event in events:
        for event_date in dates_in_month(event, year, month):
            grouped[event_date].append(event)
    return grouped


def format_event_range(event: ScheduleEvent) -> str:
    if event.start_date == event.end_date:
        return event.start_date.isoformat()
    return f"{event.start_date.isoformat()} - {event.end_date.isoformat()}"


def render_calendar(events: list[ScheduleEvent], year: int, month: int) -> None:
    cal = calendar.Calendar(firstweekday=0)
    grouped_events = events_by_day(events, year, month)

    st.subheader(f"{year}년 {month}월")
    header_columns = st.columns(7)
    for column, weekday in zip(header_columns, WEEKDAYS, strict=True):
        column.markdown(f"**{weekday}**")

    for week in cal.monthdatescalendar(year, month):
        columns = st.columns(7)
        for column, current_date in zip(columns, week, strict=True):
            in_month = current_date.month == month
            day_events = grouped_events.get(current_date, [])
            label = str(current_date.day) if in_month else f":gray[{current_date.day}]"

            with column:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    if in_month:
                        for event in day_events[:3]:
                            st.caption(event.title)
                        if len(day_events) > 3:
                            st.caption(f"외 {len(day_events) - 3}건")


def render_event_list(events: list[ScheduleEvent]) -> None:
    st.subheader("월간 일정 목록")
    if not events:
        st.info("선택한 월에 표시할 일정이 없습니다.")
        return

    rows = [
        {
            "날짜": format_event_range(event),
            "일정": event.title,
        }
        for event in events
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="학교 일정", layout="wide")
    st.title("학교 일정")

    events, error_message = load_events()
    st.caption(f"데이터 파일: `{DEFAULT_EVENTS_PATH}`")

    if error_message:
        st.warning(error_message)
        return

    years, default_year, default_month = month_options(events)
    with st.sidebar:
        st.header("표시 기준")
        selected_year = st.selectbox("연도", years, index=years.index(default_year))
        selected_month = st.selectbox("월", list(range(1, 13)), index=default_month - 1)

    month_events = [
        event
        for event in events
        if overlaps_month(event, selected_year, selected_month)
    ]

    st.metric("선택한 월 일정", len(month_events))
    render_calendar(month_events, selected_year, selected_month)
    render_event_list(month_events)


if __name__ == "__main__":
    main()
