#!/usr/bin/env bash
set -euo pipefail

uv run streamlit run src/ui/streamlit_app.py "$@"
