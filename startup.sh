#!/usr/bin/env bash
set -euo pipefail

APP_PORT="${PORT:-8000}"

python -m streamlit run agent/03_streamlit_sql_chatbot.py \
  --server.address 0.0.0.0 \
  --server.port "${APP_PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
