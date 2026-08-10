"""Central config, read from environment (.env loaded if present)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
DB_PATH = ROOT / "db" / "datagovie.sqlite"
SITE_OUT = ROOT / "docs"  # GitHub Pages (branch-deploy) only serves from / or /docs

CKAN_BASE = "https://data.gov.ie/api/3/action"
CKAN_REQUEST_DELAY_SECONDS = 1.0  # self-throttle during discovery probing

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANALYST_MODEL = os.environ.get("ANALYST_MODEL", "claude-sonnet-4-5")

ROW_CAP = 20_000
RECENCY_EXCLUSION_DAYS = 30
INTERESTINGNESS_THRESHOLD = 50

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")  # unset = notification skipped

SITE_TITLE = "Ireland Open Data Analyst"
ACCENT_COLOUR = "#8B3A2E"  # burnt red — matches the Claude-Design mockup
