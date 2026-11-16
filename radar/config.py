"""Runtime configuration, read from environment variables (GitHub Actions secrets)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("RADAR_DB", DATA_DIR / "radar.db"))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Cheap model for the per-document read; override with RADAR_MODEL if needed.
MODEL = os.environ.get("RADAR_MODEL", "claude-haiku-5-5")

BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY", "")
# "draft" = create the issue in Buttondown for review; "send" = send automatically.
DELIVERY_MODE = os.environ.get("RADAR_DELIVERY_MODE", "draft")

USER_AGENT = os.environ.get(
    "RADAR_USER_AGENT",
    "CouncilRadar/0.1 (public-records monitoring; contact via repository)",
)
REQUEST_DELAY_SECONDS = float(os.environ.get("RADAR_DELAY", "2.0"))
LOOKBACK_DAYS = int(os.environ.get("RADAR_LOOKBACK_DAYS", "21"))
LOOKAHEAD_DAYS = int(os.environ.get("RADAR_LOOKAHEAD_DAYS", "21"))
MAX_DOC_PAGES = int(os.environ.get("RADAR_MAX_DOC_PAGES", "400"))
