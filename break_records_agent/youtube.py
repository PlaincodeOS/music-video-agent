"""YouTube search and download helpers."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Iterable, List

from break_records_agent.models import ClipCandidate, DownloadedClip


LOGGER = logging.getLogger(__name__)


async def search_clips(
    query: str,
    limit: int = 5,
) -> List[ClipCandidate]:
    try:
        from youtubesearchpython.__future__ import VideosSearch
    except ImportError:
        return await asyncio.to_thread(search_clips_sync, query=query, limit=limit)

    search = VideosSearch(query, limit=limit)
    response = await search.next()
    return parse_search_response(response)


def search_clips_sync(query: str, limit: int) -> List[ClipCandidate]:
    try:
        from youtubesearchpython import VideosSearch
    except ImportError as exc:
        raise RuntimeError(
            "Missing youtube-search-python package. Activate .venv and run: "
            "pip install -r requirements.txt"
        ) from exc

    response = VideosSearch(query, limit=limit).result()
    return parse_search_response(response)


def parse_search_response(response: dict) -> List[ClipCandidate]:
    candidates: List[ClipCandidate] = []
    for item in response.get("result", []):
        link = item.get("link")
        title = item.get("title")
        if not link or not title:
            continue
        candidates.append(
            ClipCandidate(
                title=title,
                url=link,
                duration=item.get("duration") or "",
            )
        )
    return candidates


async def download_clips(
    candidates: Iterable[ClipCandidate],
    work_dir: Path,
    clip_seconds: float,
    max_clips: int,
) -> List[DownloadedClip]:
    work_dir.mkdir(parents=True, exist_ok=True)
    downloaded: List[DownloadedClip] = []

    for candidate in candidates:
        if len(downloaded) >= max_clips:
            break

        index = len(downloaded)
        try:
            clip = await asyncio.to_thread(
                download_one_clip,
                candidate=candidate,
                work_dir=work_dir,
                clip_seconds=clip_seconds,
                index=index,
            )
        except Exception as exc:
            LOGGER.warning("Skipping failed download for '%s': %s", candidate.title, exc)
            continue

        LOGGER.info("Downloaded clip %s: %s", index + 1, candidate.title)
        downloaded.append(clip)

    return downloaded


def download_one_clip(
    candidate: ClipCandidate,
    work_dir: Path,
    clip_seconds: float,
    index: int,
) -> DownloadedClip:
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import download_range_func
    except ImportError as exc:
        raise RuntimeError(
            "Missing yt-dlp package. Activate .venv and run: pip install -r requirements.txt"
        ) from exc

    stem = f"clip_{index:02d}"
    outtmpl = str(work_dir / f"{stem}.%(ext)s")
    ydl_opts = {
        "download_ranges": download_range_func(None, [(0, clip_seconds)]),
        "force_keyframes_at_cuts": True,
        "format": "bv*[height<=1080]+ba/b[height<=1080]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "no_warnings": True,
        "outtmpl": outtmpl,
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(candidate.url, download=True)

    files = [
        path
        for path in work_dir.glob(f"{stem}.*")
        if path.is_file() and not path.name.endswith((".part", ".ytdl"))
    ]
    if not files:
        raise RuntimeError("yt-dlp completed but no media file was created.")

    media_path = max(files, key=lambda path: path.stat().st_mtime)
    title = info.get("title") or candidate.title
    duration = str(info.get("duration") or candidate.duration or "")
    downloaded_candidate = ClipCandidate(title=title, url=candidate.url, duration=duration)
    return DownloadedClip(candidate=downloaded_candidate, path=media_path, index=index)
