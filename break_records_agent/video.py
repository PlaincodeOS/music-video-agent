"""FFmpeg rendering and composition helpers."""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

from break_records_agent.models import DownloadedClip, Overlay


LOGGER = logging.getLogger(__name__)
WIDTH = 1080
HEIGHT = 1920
FONT_SIZE = 54


def compose_portrait_video(
    clips: Iterable[DownloadedClip],
    overlays: Iterable[Overlay],
    output_path: Path,
    render_dir: Path,
    clip_seconds: float,
) -> Path:
    render_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    overlay_by_index = {overlay.clip.index: overlay for overlay in overlays}
    rendered_paths: List[Path] = []

    for clip in clips:
        overlay = overlay_by_index[clip.index]
        rendered = render_clip(
            clip=clip,
            overlay_text=overlay.text,
            render_dir=render_dir,
            clip_seconds=clip_seconds,
        )
        rendered_paths.append(rendered)

    concat_videos(rendered_paths, output_path)
    validate_output(output_path)
    return output_path


def render_clip(
    clip: DownloadedClip,
    overlay_text: str,
    render_dir: Path,
    clip_seconds: float,
) -> Path:
    output = render_dir / f"rendered_{clip.index:02d}.mp4"
    text_file = render_dir / f"dialogue_{clip.index:02d}.txt"
    text_file.write_text(overlay_text, encoding="utf-8")
    drawtext = build_drawtext_filter(text_file)
    filters = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,{drawtext}"
    )

    cmd = ["ffmpeg", "-y", "-i", str(clip.path)]
    if not has_audio_stream(clip.path):
        cmd.extend(
            [
                "-f",
                "lavfi",
                "-t",
                str(clip_seconds),
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
            ]
        )
        audio_map = ["-map", "1:a:0"]
    else:
        audio_map = ["-map", "0:a:0?"]

    cmd.extend(
        [
            "-t",
            str(clip_seconds),
            "-vf",
            filters,
            "-map",
            "0:v:0",
            *audio_map,
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            str(output),
        ]
    )
    run_command(cmd)
    return output


def concat_videos(rendered_paths: List[Path], output_path: Path) -> None:
    concat_file = output_path.parent / "concat.txt"
    lines = [f"file {shlex.quote(str(path.resolve()))}" for path in rendered_paths]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_path),
    ]
    run_command(cmd)


def build_drawtext_filter(text_file: Path) -> str:
    font = find_font_file()
    options = [
        f"textfile='{escape_drawtext_text(str(text_file.resolve()))}'",
        "fontcolor=white",
        f"fontsize={FONT_SIZE}",
        "x=(w-text_w)/2",
        "y=h-text_h-190",
        "line_spacing=12",
    ]
    if font:
        options.insert(0, f"fontfile='{escape_drawtext_text(str(font))}'")
    return "drawtext=" + ":".join(options)


def escape_drawtext_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", " ")
    )


def find_font_file() -> Optional[Path]:
    candidates = [
        Path("/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    LOGGER.warning("No bold font file found; FFmpeg will use its default drawtext font.")
    return None


def has_audio_stream(path: Path) -> bool:
    try:
        import ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "Missing ffmpeg-python package. Activate .venv and run: pip install -r requirements.txt"
        ) from exc

    probe = ffmpeg.probe(str(path))
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def validate_output(path: Path) -> None:
    try:
        import ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "Missing ffmpeg-python package. Activate .venv and run: pip install -r requirements.txt"
        ) from exc

    probe = ffmpeg.probe(str(path))
    video_stream = next(
        stream for stream in probe["streams"] if stream.get("codec_type") == "video"
    )
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    duration = float(probe["format"].get("duration", 0))

    if (width, height) != (WIDTH, HEIGHT):
        raise RuntimeError(f"Output is {width}x{height}, expected {WIDTH}x{HEIGHT}.")
    if not 15 <= duration <= 30:
        LOGGER.warning("Output duration is %.2fs, outside the 15-30s target.", duration)


def run_command(cmd: List[str]) -> None:
    LOGGER.debug("Running command: %s", " ".join(shlex.quote(part) for part in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr)
