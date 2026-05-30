"""Shared data models for the video agent pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClipCandidate:
    title: str
    url: str
    duration: str = ""


@dataclass(frozen=True)
class DownloadedClip:
    candidate: ClipCandidate
    path: Path
    index: int


@dataclass(frozen=True)
class Overlay:
    clip: DownloadedClip
    text: str
