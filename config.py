import os

# Load tokens from environment variables (secure for Render deployment)
# Falls back to hardcoded values for local development only
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8408479766:AAEIQEm2LWHwegYdAev45JgVekN3XLd23W0")
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "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")

# Validate required tokens
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is required!")
