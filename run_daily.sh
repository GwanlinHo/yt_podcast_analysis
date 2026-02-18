#!/bin/bash
set -e  # Exit on error

echo "=== [1/3] Fetching latest videos... ==="
uv run daily_update.py

echo "=== [2/3] Generating HTML report... ==="
uv run generate_report.py

echo "=== [3/3] Syncing to Git... ==="
./sync.sh

echo "=== ✅ Daily Routine Completed Successfully! ==="
