from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import streamlit as st
import yaml
from streamlit_calendar import calendar as streamlit_calendar


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHOOLS_CONFIG_PATH = PROJECT_ROOT / "src" / "config" / "streamlit_schools.yml"


@dataclass(frozen=True)
class ScheduleEvent:
    title: str
    start_date: date
    end_date: date
    school_name: str | None = None


@dataclass(frozen=True)
class SchoolCalendar:
    name: str
    events_path: Path


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_school_calendars(
    path: Path = SCHOOLS_CONFIG_PATH,
) -> tuple[list[SchoolCalendar], str | None, str | None]:
    if not path.exists():
        return [], None, f"학교 목록 설정 파일을 찾을 수 없습니다: {path}"

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [], None, f"학교 목록 설정 파일의 YAML 형식이 올바르지 않습니다: {exc}"

    if not isinstance(data, dict):
        return [], None, "학교 목록 설정 파일의 최상위 형식은 매핑이어야 합니다."

    default_school = data.get("default_school")
    if default_school is not None and not isinstance(default_school, str):
        return [], None, "`default_school` 값은 문자열이어야 합니다."

    raw_schools = data.get("schools")
    if not isinstance(raw_schools, list) or not raw_schools:
        return [], None, "`schools` 목록에 학교를 하나 이상 설정해야 합니다."

    schools: list[SchoolCalendar] = []
    seen_names: set[str] = set()
    for index, raw_school in enumerate(raw_schools, start=1):
        if not isinstance(raw_school, dict):
            return [], None, f"{index}번째 학교 설정 형식이 올바르지 않습니다."

        name = raw_school.get("name")
        events_path = raw_school.get("events_path")
        if not isinstance(name, str) or not name.strip():
            return [], None, f"{index}번째 학교의 `name` 값이 올바르지 않습니다."
        if not isinstance(events_path, str) or not events_path.strip():
            return [], None, f"{index}번째 학교의 `events_path` 값이 올바르지 않습니다."

        school_name = name.strip()
        if school_name in seen_names:
            return [], None, f"학교 이름이 중복되었습니다: {school_name}"
        seen_names.add(school_name)
        schools.append(
            SchoolCalendar(
                name=school_name,
                events_path=resolve_project_path(events_path.strip()),
            )
        )

    if default_school and default_school not in seen_names:
        return [], None, f"기본 학교가 `schools` 목록에 없습니다: {default_school}"

    return schools, default_school or schools[0].name, None


def load_events(path: Path, school_name: str | None = None) -> tuple[list[ScheduleEvent], str | None]:
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

        events.append(
            ScheduleEvent(
                title=title,
                start_date=start_date,
                end_date=end_date,
                school_name=school_name,
            )
        )

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


def to_calendar_event(
    event: ScheduleEvent,
    color: str | None = None,
    prefix_school: bool = False,
) -> dict[str, object]:
    title = f"[{event.school_name}] {event.title}" if prefix_school and event.school_name else event.title
    resolved_color = color or event_color(event.title)
    return {
        "title": title,
        "start": event.start_date.isoformat(),
        "end": (event.end_date + timedelta(days=1)).isoformat(),
        "allDay": True,
        "backgroundColor": resolved_color,
        "borderColor": resolved_color,
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


def render_legend(schools: list[str], school_colors: dict[str, str]) -> None:
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">'
    for school in schools:
        color = school_colors.get(school, "#16a34a")
        legend_html += (
            f'<div style="display: flex; align-items: center; gap: 5px;">'
            f'<span style="display: inline-block; width: 14px; height: 14px; '
            f'background-color: {color}; border-radius: 3px;"></span>'
            f'<span style="font-size: 14px; font-weight: 500;">{school}</span>'
            f'</div>'
        )
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)


def render_calendar(
    events: list[ScheduleEvent],
    year: int,
    month: int,
    school_name: str,
    school_colors: dict[str, str] | None = None,
    prefix_school: bool = False,
    selected_schools: list[str] | None = None,
) -> dict | None:
    st.subheader("월간 달력")
    if school_colors and selected_schools:
        render_legend(selected_schools, school_colors)

    calendar_events = []
    for event in events:
        color = school_colors.get(event.school_name) if (school_colors and event.school_name) else None
        calendar_events.append(to_calendar_event(event, color=color, prefix_school=prefix_school))

    calendar_result = streamlit_calendar(
        events=calendar_events,
        options=calendar_options(year, month),
        key=f"school-calendar-{school_name}-{year}-{month}",
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


def render_event_list(events: list[ScheduleEvent], show_school: bool = False) -> None:
    st.subheader("월간 일정 목록")
    if not events:
        st.info("선택한 월에 표시할 일정이 없습니다.")
        return

    if show_school:
        rows = [
            {
                "학교": event.school_name or "",
                "날짜": format_event_range(event),
                "일정": event.title,
            }
            for event in events
        ]
    else:
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
    schools, default_school, school_config_error = load_school_calendars()
    if school_config_error:
        st.warning(school_config_error)
        return

    school_names = [school.name for school in schools]
    school_by_name = {school.name: school for school in schools}
    default_school_index = school_names.index(default_school or school_names[0])

    with st.sidebar:
        st.header("표시 기준")
        compare_mode = st.checkbox("여러 학교 일정 함께 보기 (통합 모드)", value=False)
        if compare_mode:
            selected_schools = st.multiselect(
                "학교 선택",
                school_names,
                default=[default_school] if default_school in school_names else [school_names[0]],
            )
        else:
            selected_school = st.selectbox(
                "학교",
                school_names,
                index=default_school_index,
            )
            selected_schools = [selected_school]

    if not selected_schools:
        st.warning("조회할 학교를 하나 이상 선택해 주세요.")
        return

    # 학교별 고유 색상 맵 정의 (6가지 파스텔 톤 색상)
    SCHOOL_COLORS = [
        "#2563eb",  # Blue
        "#8b5cf6",  # Purple
        "#ec4899",  # Pink
        "#f59e0b",  # Amber
        "#10b981",  # Green
        "#06b6d4",  # Cyan
    ]
    school_colors = {
        name: SCHOOL_COLORS[i % len(SCHOOL_COLORS)]
        for i, name in enumerate(school_names)
    }

    # 선택된 학교들의 모든 일정 취합
    all_events: list[ScheduleEvent] = []
    loaded_schools_paths = []
    for school_name in selected_schools:
        school_cal = school_by_name[school_name]
        events_path = school_cal.events_path
        loaded_schools_paths.append(f"`{school_cal.name}` (`{events_path.name}`)")

        events, error_message = load_events(events_path, school_name=school_name)
        if error_message:
            st.warning(f"{school_name} 일정 로드 실패: {error_message}")
            return
        all_events.extend(events)

    # 전체 일정을 날짜 및 제목순으로 정렬
    all_events.sort(key=lambda event: (event.start_date, event.end_date, event.title))

    if len(selected_schools) == 1:
        st.title(f"{selected_schools[0]} 학교 일정")
        st.caption(f"데이터 파일: {loaded_schools_paths[0]}")
    else:
        st.title("통합 학교 일정 비교")
        st.caption(f"로드된 학교: {', '.join(loaded_schools_paths)}")

    if not all_events:
        st.info("선택한 학교들의 전체 일정이 없습니다.")
        return

    years, default_year, default_month = month_options(all_events)
    with st.sidebar:
        selected_year = st.selectbox("연도", years, index=years.index(default_year) if default_year in years else 0)
        selected_month = st.selectbox("월", list(range(1, 13)), index=default_month - 1)

    use_school_colors = len(selected_schools) > 1
    prefix_school = len(selected_schools) > 1

    calendar_result = render_calendar(
        all_events,
        selected_year,
        selected_month,
        school_name="-".join(selected_schools),
        school_colors=school_colors if use_school_colors else None,
        prefix_school=prefix_school,
        selected_schools=selected_schools,
    )

    list_year, list_month = month_from_calendar_result(
        calendar_result,
        selected_year,
        selected_month,
    )
    month_events = [
        event
        for event in all_events
        if overlaps_month(event, list_year, list_month)
    ]

    st.metric("선택한 월 일정", len(month_events))
    render_event_list(month_events, show_school=use_school_colors)


if __name__ == "__main__":
    main()
