#!/bin/bash
set -e  # Exit on error

echo "=== [1/3] Fetching latest videos... ==="
python3 daily_update.py

echo "=== [2/3] Generating HTML report... ==="
python3 generate_report.py

echo "=== [3/3] Syncing to Git... ==="
./sync.sh

echo "=== ✅ Daily Routine Completed Successfully! ==="
