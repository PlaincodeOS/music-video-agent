from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from break_records_agent.runner import RunRequest, run_generation_sync


@dataclass(frozen=True)
class ApiRequest:
    artist: str
    profile: str = "gen_z_rnb"
    age_range: Optional[str] = None
    genres: Optional[Iterable[str]] = None
    mood: Optional[str] = None
    search_limit: int = 5
    clip_count: int = 3
    clip_seconds: float = 10.0
    mock_overlays: bool = False
    drive_folder_id: Optional[str] = None


def build_request_from_payload(payload: dict) -> ApiRequest:
    artist = (payload.get("artist") or "").strip()
    if not artist:
        raise ValueError("artist is required")

    genres = payload.get("genres")
    if isinstance(genres, str):
        genres = [item.strip() for item in genres.split(",") if item.strip()]

    return ApiRequest(
        artist=artist,
        profile=(payload.get("profile") or "gen_z_rnb").strip(),
        age_range=payload.get("age_range"),
        genres=genres,
        mood=payload.get("mood"),
        search_limit=int(payload.get("search_limit", 5)),
        clip_count=int(payload.get("clip_count", 3)),
        clip_seconds=float(payload.get("clip_seconds", 10.0)),
        mock_overlays=parse_bool(payload.get("mock_overlays", False)),
        drive_folder_id=payload.get("drive_folder_id"),
    )


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def run_generation(request: ApiRequest):
    run_request = RunRequest(
        artist=request.artist,
        profile_key=request.profile,
        age_range=request.age_range,
        genres=request.genres,
        mood=request.mood,
        search_limit=request.search_limit,
        clip_count=request.clip_count,
        clip_seconds=request.clip_seconds,
        mock_overlays=request.mock_overlays,
        drive_folder_id=request.drive_folder_id,
    )
    return run_generation_sync(run_request)
