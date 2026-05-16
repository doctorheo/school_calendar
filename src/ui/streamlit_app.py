from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import streamlit as st
from streamlit_calendar import calendar as streamlit_calendar


DEFAULT_EVENTS_PATH = Path(__file__).resolve().parents[2] / "src" / "parse" / "output" / "merged_events.json"


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


def format_event_range(event: ScheduleEvent) -> str:
    if event.start_date == event.end_date:
        return event.start_date.isoformat()
    return f"{event.start_date.isoformat()} - {event.end_date.isoformat()}"


def event_color(title: str) -> str:
    if "방학" in title:
        return "#2563eb"
    if "휴업일" in title:
        return "#64748b"
    if any(keyword in title for keyword in ("설날", "신정", "공휴일")):
        return "#dc2626"
    return "#16a34a"


def to_calendar_event(event: ScheduleEvent) -> dict[str, object]:
    color = event_color(event.title)
    return {
        "title": event.title,
        "start": event.start_date.isoformat(),
        "end": (event.end_date + timedelta(days=1)).isoformat(),
        "allDay": True,
        "backgroundColor": color,
        "borderColor": color,
    }


def calendar_options(year: int, month: int) -> dict[str, object]:
    return {
        "initialView": "dayGridMonth",
        "initialDate": date(year, month, 1).isoformat(),
        "locale": "ko",
        "height": "auto",
        "editable": False,
        "selectable": False,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "",
        },
        "buttonText": {
            "today": "오늘",
        },
        "dayMaxEvents": True,
    }


def render_calendar(events: list[ScheduleEvent], year: int, month: int) -> dict | None:
    st.subheader("월간 달력")
    calendar_result = streamlit_calendar(
        events=[to_calendar_event(event) for event in events],
        options=calendar_options(year, month),
        key=f"school-calendar-{year}-{month}",
    )
    return calendar_result if isinstance(calendar_result, dict) else None


def month_from_calendar_result(calendar_result: dict | None, default_year: int, default_month: int) -> tuple[int, int]:
    if not calendar_result:
        return default_year, default_month

    view = None
    for value in calendar_result.values():
        if isinstance(value, dict) and isinstance(value.get("view"), dict):
            view = value["view"]
            break

    if not isinstance(view, dict):
        return default_year, default_month

    current_start = view.get("currentStart")
    if not isinstance(current_start, str):
        return default_year, default_month

    try:
        current_date = datetime.fromisoformat(current_start.replace("Z", "+00:00")).date()
    except ValueError:
        return default_year, default_month

    return current_date.year, current_date.month


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

    calendar_result = render_calendar(events, selected_year, selected_month)
    list_year, list_month = month_from_calendar_result(
        calendar_result,
        selected_year,
        selected_month,
    )
    month_events = [
        event
        for event in events
        if overlaps_month(event, list_year, list_month)
    ]

    st.metric("선택한 월 일정", len(month_events))
    render_event_list(month_events)


if __name__ == "__main__":
    main()
