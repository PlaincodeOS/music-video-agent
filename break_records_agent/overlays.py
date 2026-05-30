"""Claude Haiku music video text overlay generation."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Iterable, List

from break_records_agent.models import DownloadedClip, Overlay
from break_records_agent.profiles import DemographicProfile


LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL = "claude-3-haiku-20240307"


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def fallback_overlay(artist: str, profile: DemographicProfile, clip: DownloadedClip) -> str:
    templates = [
        f"{artist} hits different late at night",
        "When the beat drops, everything fades",
        "Songs that make you feel alive",
        "This energy is unmatched",
        "A whole aesthetic",
    ]
    offset = sum(ord(c) for c in artist) % len(templates)
    return templates[(clip.index + offset) % len(templates)]


def clean_overlay_text(text: str) -> str:
    """Extract a single line of clean text without quotes or markdown."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = text.replace('"', '').replace("'", "").strip()
    
    # Just take the first non-empty line
    lines = [L for L in text.splitlines() if L.strip()]
    if not lines:
        return ""
        
    line = lines[0]
    line = re.sub(r"^\d+[\).\s-]+", "", line)
    return line.lstrip("- ").strip()


async def generate_overlays(
    artist: str,
    profile: DemographicProfile,
    clips: Iterable[DownloadedClip],
    mock: bool = False,
) -> List[Overlay]:
    clip_list = list(clips)
    load_dotenv_if_available()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if mock or not api_key:
        if not api_key and not mock:
            LOGGER.warning("ANTHROPIC_API_KEY is missing; using mock overlays.")
        return [
            Overlay(clip=clip, text=fallback_overlay(artist, profile, clip))
            for clip in clip_list
        ]

    try:
        from anthropic import AsyncAnthropic
    except ImportError as exc:
        raise RuntimeError(
            "Missing anthropic package. Activate .venv and run: pip install -r requirements.txt"
        ) from exc

    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = AsyncAnthropic(api_key=api_key)
    
    tasks = [
        generate_one_overlay(
            client=client,
            artist=artist,
            profile=profile,
            clip=clip,
            model=model,
        )
        for clip in clip_list
    ]
    return await asyncio.gather(*tasks)


async def generate_one_overlay(
    client: object,
    artist: str,
    profile: DemographicProfile,
    clip: DownloadedClip,
    model: str,
) -> Overlay:
    genre_str = ", ".join(profile.genres)
    prompt = (
        f"Write a 1-line text overlay for {profile.age_range} year olds who like {genre_str}.\n"
        f"Artist: {artist}\n"
        f"Clip: {clip.candidate.title}\n"
        f"Vibe: {profile.mood}\n"
        "Max 8 words. Return ONLY the overlay text without quotes, labels, or extra formatting. No emojis."
    )

    response = await client.messages.create(
        model=model,
        max_tokens=60,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    
    text = response.content[0].text if response.content else ""
    cleaned = clean_overlay_text(text)
    if not cleaned:
        cleaned = fallback_overlay(artist, profile, clip)
        
    return Overlay(clip=clip, text=cleaned)
