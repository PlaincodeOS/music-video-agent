"""Shared generation runner for CLI and Django."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from break_records_agent.config import AgentConfig
from break_records_agent.drive import DriveUploadResult, upload_file_to_drive
from break_records_agent.overlays import generate_overlays
from break_records_agent.profiles import DemographicProfile, get_profile
from break_records_agent.video import compose_portrait_video
from break_records_agent.youtube import download_clips, search_clips


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunRequest:
    artist: str
    profile_key: str = "gen_z_rnb"
    age_range: Optional[str] = None
    genres: Optional[Iterable[str]] = None
    mood: Optional[str] = None
    search_limit: int = 5
    clip_count: int = 3
    clip_seconds: float = 10.0
    mock_overlays: bool = False
    drive_folder_id: Optional[str] = None


def build_profile(request: RunRequest) -> DemographicProfile:
    base = get_profile(request.profile_key)
    if not any([request.age_range, request.genres, request.mood]):
        return base

    genres = tuple(request.genres) if request.genres else base.genres
    return DemographicProfile(
        key="custom",
        label=f"Custom profile based on {base.label}",
        age_range=request.age_range or base.age_range,
        genres=genres,
        mood=request.mood or base.mood,
    )


def default_output_path(artist: str, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", artist.strip().lower()).strip("_")
    return output_dir / f"{slug or 'artist'}_{timestamp}.mp4"


def build_music_query(artist: str, profile: DemographicProfile) -> str:
    genre_terms = " ".join(profile.genres)
    return f"{artist} official music video live performance {genre_terms} {profile.mood}"


async def run_generation(request: RunRequest) -> DriveUploadResult:
    profile = build_profile(request)

    with tempfile.TemporaryDirectory(prefix="break-records-") as temp_dir:
        work_dir = Path(temp_dir) / "work"
        output_dir = Path(temp_dir) / "output"

        config = AgentConfig(
            clip_count=request.clip_count,
            clip_seconds=request.clip_seconds,
            output_dir=output_dir,
            search_limit=request.search_limit,
            work_dir=work_dir,
        )

        output_path = default_output_path(request.artist, output_dir)
        query = build_music_query(request.artist, profile)

        LOGGER.info("Searching YouTube for %s clips: %s", config.search_limit, query)
        candidates = await search_clips(query, limit=config.search_limit)
        if not candidates:
            raise RuntimeError("No YouTube results were found. Try a different artist or profile.")

        LOGGER.info("Downloading up to %s usable clips.", config.clip_count)
        downloaded = await download_clips(
            candidates=candidates,
            work_dir=config.download_dir,
            clip_seconds=config.clip_seconds,
            max_clips=config.clip_count,
        )
        if len(downloaded) < 2:
            raise RuntimeError(
                f"Only downloaded {len(downloaded)} usable clip(s). At least 2 are needed."
            )

        LOGGER.info("Generating text overlays.")
        overlays = await generate_overlays(
            artist=request.artist,
            profile=profile,
            clips=downloaded,
            mock=request.mock_overlays,
        )

        LOGGER.info("Composing final portrait MP4.")
        result_path = compose_portrait_video(
            clips=downloaded,
            overlays=overlays,
            output_path=output_path,
            render_dir=config.render_dir,
            clip_seconds=config.clip_seconds,
        )

        LOGGER.info("Uploading final MP4 to Google Drive.")
        folder_id = request.drive_folder_id or os.getenv("GDRIVE_FOLDER_ID")
        return upload_file_to_drive(result_path, folder_id=folder_id)


def run_generation_sync(request: RunRequest) -> DriveUploadResult:
    return asyncio.run(run_generation(request))
