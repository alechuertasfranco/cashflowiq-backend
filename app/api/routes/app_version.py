"""app/api/routes/app_version.py

Public endpoint the Flutter app polls on startup to check for a newer APK.
Reads releases/version.json fresh on every request so a new release doesn't
require restarting the backend container - just editing that file.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/app", tags=["App Version"])

VERSION_FILE = Path(__file__).resolve().parents[3] / "releases" / "version.json"


@router.get("/version")
def get_latest_version():
    if not VERSION_FILE.exists():
        raise HTTPException(status_code=404, detail="No release published yet")

    with VERSION_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)
