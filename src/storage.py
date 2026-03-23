"""File-backed storage helpers for activities and users."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
DB_FILE = DATA_DIR / "db.json"
SEED_FILE = DATA_DIR / "seed_db.json"

_DB_LOCK = Lock()


def _seed_data() -> dict[str, Any]:
    if not SEED_FILE.exists():
        return {"users": {}, "activities": {}}
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


def _write_db(db: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


def _read_db() -> dict[str, Any]:
    if not DB_FILE.exists():
        _write_db(_seed_data())
    return json.loads(DB_FILE.read_text(encoding="utf-8"))


def _ensure_shape(db: dict[str, Any]) -> dict[str, Any]:
    db.setdefault("users", {})
    db.setdefault("activities", {})
    return db


def get_activities() -> dict[str, Any]:
    with _DB_LOCK:
        db = _ensure_shape(_read_db())
        return db["activities"]


def signup_for_activity(activity_name: str, email: str) -> None:
    with _DB_LOCK:
        db = _ensure_shape(_read_db())
        activities = db["activities"]

        if activity_name not in activities:
            raise KeyError("activity_not_found")

        participants = activities[activity_name].setdefault("participants", [])
        if email in participants:
            raise ValueError("already_signed_up")

        participants.append(email)

        # Keep a lightweight user record for future account/profile work.
        if email not in db["users"]:
            db["users"][email] = {
                "email": email,
                "name": "",
                "grade": "",
            }

        _write_db(db)


def unregister_from_activity(activity_name: str, email: str) -> None:
    with _DB_LOCK:
        db = _ensure_shape(_read_db())
        activities = db["activities"]

        if activity_name not in activities:
            raise KeyError("activity_not_found")

        participants = activities[activity_name].setdefault("participants", [])
        if email not in participants:
            raise ValueError("not_signed_up")

        participants.remove(email)
        _write_db(db)


def seed_db(force: bool = False) -> None:
    with _DB_LOCK:
        if force or not DB_FILE.exists():
            _write_db(_seed_data())
