from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from schemas import Profile, Lesson, Result


DB_FILE = Path(__file__).parent / "learnmate_db.json"


class LocalDatabase:
    """Lightweight JSON-backed local storage for LearnMate sessions and records."""

    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._profiles: dict[str, dict] = {}
        self._lessons: dict[str, dict] = {}
        self._results: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._profiles = data.get("profiles", {})
                    self._lessons = data.get("lessons", {})
                    self._results = data.get("results", [])
            except Exception:
                # If file is corrupted or unreadable, start fresh
                self._profiles = {}
                self._lessons = {}
                self._results = []

    def _save(self) -> None:
        data = {
            "profiles": self._profiles,
            "lessons": self._lessons,
            "results": self._results,
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # --- Profile Operations ---
    def save_profile(self, profile: Profile) -> None:
        self._profiles[profile.user_id] = profile.model_dump()
        self._save()

    def get_profile(self, user_id: str) -> Optional[Profile]:
        data = self._profiles.get(user_id)
        if data:
            return Profile.model_validate(data)
        return None

    # --- Lesson Operations ---
    def save_lesson(self, lesson: Lesson) -> None:
        self._lessons[lesson.id] = lesson.model_dump()
        self._save()

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        data = self._lessons.get(lesson_id)
        if data:
            return Lesson.model_validate(data)
        return None

    def get_latest_lesson(self) -> Optional[Lesson]:
        if not self._lessons:
            return None
        last_item = list(self._lessons.values())[-1]
        return Lesson.model_validate(last_item)

    # --- Result Operations ---
    def save_result(self, result: Result) -> None:
        self._results.append(result.model_dump())
        self._save()

    def get_results(self) -> list[Result]:
        return [Result.model_validate(r) for r in self._results]

    def get_latest_result(self) -> Optional[Result]:
        if not self._results:
            return None
        return Result.model_validate(self._results[-1])


# Global database instance
db = LocalDatabase()
