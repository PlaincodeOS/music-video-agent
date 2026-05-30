"""Runtime configuration for the Break Records video agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentConfig:
    """Settings that control a single generated video run."""

    clip_count: int
    clip_seconds: float
    output_dir: Path
    search_limit: int
    work_dir: Path
    width: int = 1080
    height: int = 1920
    font_size: int = 54

    @property
    def download_dir(self) -> Path:
        return self.work_dir / "downloads"

    @property
    def render_dir(self) -> Path:
        return self.work_dir / "rendered"

    @property
    def frame_dir(self) -> Path:
        return self.work_dir / "frames"
