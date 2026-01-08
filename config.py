import os
import sys

# Load token from Render environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Safety check: Stop immediately if token is missing to avoid crashing later
if not TELEGRAM_TOKEN:
    print("❌ CRITICAL ERROR: TELEGRAM_TOKEN not found in environment variables!")
    print("Please add it in Render Dashboard > Environment.")
