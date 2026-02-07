import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (CXC-AI-Hackathon/)
# Path: edgeaudit/backend/app/core/config.py -> parents[4] -> CXC-AI-Hackathon/
_env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(_env_path)


class Settings:
    # Snowflake
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER", "")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD", "")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE", "")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE", "")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA", "")

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Backboard
    BACKBOARD_API_KEY: str = os.getenv("BACKB_API", "")
    BACKBOARD_BASE_URL: str = os.getenv(
        "BACKBOARD_BASE_URL", "https://api.backboard.io/v1"
    )

    # App
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")


settings = Settings()
