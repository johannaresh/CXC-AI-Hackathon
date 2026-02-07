from fastapi import APIRouter

from ..core.config import settings
from ..services.snowflake_client import is_connected as snowflake_connected
from ..services.backboard_client import is_configured as backboard_configured

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "snowflake_connected": snowflake_connected(),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "backboard_configured": backboard_configured(),
    }
