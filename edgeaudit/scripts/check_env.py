"""
Diagnostic script to verify environment configuration for EdgeAudit.
Run this to check if your .env file is being loaded correctly.
"""

import sys
from pathlib import Path

# Add the edgeaudit directory to sys.path so we can import backend modules
# This script is in edgeaudit/scripts/, so we go up one level to get to edgeaudit/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings
from backend.app.services.snowflake_client import is_connected, _is_configured
from backend.app.services.gemini_client import is_configured as gemini_is_configured

print("=" * 80)
print("EdgeAudit Environment Configuration Diagnostic")
print("=" * 80)

# Check .env path (matching the logic in config.py)
config_file = Path(__file__).resolve().parent.parent / "backend" / "app" / "core" / "config.py"
env_path = config_file.parents[4] / ".env"

print(f"\n📁 File Paths:")
print(f"   This script: {Path(__file__).resolve()}")
print(f"   Config file: {config_file}")
print(f"   Looking for .env at: {env_path}")
print(f"   .env file exists: {env_path.exists()}")
if env_path.exists():
    print(f"   .env file size: {env_path.stat().st_size} bytes")

# Check Snowflake configuration
print(f"\n❄️  Snowflake Configuration:")
print(f"   Account: {'✓ SET' if settings.SNOWFLAKE_ACCOUNT else '✗ NOT SET'}")
print(f"   User: {'✓ SET' if settings.SNOWFLAKE_USER else '✗ NOT SET'}")
print(f"   Password: {'✓ SET' if settings.SNOWFLAKE_PASSWORD else '✗ NOT SET'}")
print(f"   Warehouse: {'✓ SET' if settings.SNOWFLAKE_WAREHOUSE else '✗ NOT SET'}")
print(f"   Database: {'✓ SET' if settings.SNOWFLAKE_DATABASE else '✗ NOT SET'}")
print(f"   Schema: {'✓ SET' if settings.SNOWFLAKE_SCHEMA else '✗ NOT SET'}")

if _is_configured():
    print(f"   Configuration Status: ✓ CONFIGURED")
    print(f"   Connection Test: ", end="")
    try:
        if is_connected():
            print("✓ CONNECTED")
        else:
            print("✗ FAILED TO CONNECT")
    except Exception as e:
        print(f"✗ ERROR: {e}")
else:
    print(f"   Configuration Status: ✗ NOT CONFIGURED")

# Check Gemini configuration
print(f"\n🤖 Gemini Configuration:")
print(f"   API Key: {'✓ SET' if settings.GEMINI_API_KEY else '✗ NOT SET'}")
print(f"   Configuration Status: {'✓ CONFIGURED' if gemini_is_configured() else '✗ NOT CONFIGURED'}")

# Check Backboard configuration
print(f"\n📊 Backboard Configuration:")
print(f"   API Key: {'✓ SET' if settings.BACKBOARD_API_KEY else '✗ NOT SET'}")
print(f"   Base URL: {settings.BACKBOARD_BASE_URL}")

print("\n" + "=" * 80)

# Provide recommendations
if not _is_configured():
    print("\n⚠️  RECOMMENDATION:")
    print("   Your Snowflake credentials are not being loaded.")
    print("   Please check:")
    print(f"   1. Verify .env file exists at: {env_path}")
    print("   2. Ensure variables are named correctly (SNOWFLAKE_ACCOUNT, etc.)")
    print("   3. Restart your backend server after editing .env")
    print("   4. Make sure there are no quotes around values in .env")

if not gemini_is_configured():
    print("\n💡 NOTE:")
    print("   Gemini API key not configured - audits will use fallback narratives")

print("=" * 80)
