"""Create database tables for local development.

Run this script from the project root after DATABASE_URL is present in your
`.env` file.
"""

import sys
from pathlib import Path


# Make `backend/app` importable when this script is run from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import create_tables  # noqa: E402


if __name__ == "__main__":
    create_tables()
    print("Database tables are ready.")
