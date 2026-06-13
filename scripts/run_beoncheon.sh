#!/usr/bin/env bash
set -euo pipefail

uv run python -m src.main --config src/config/beoncheon_calendar.yml
uv run python -m src.calendar.merge_events --config src/config/beoncheon_merge_events.yml
