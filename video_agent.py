"""CLI entry point for the Break Records AI Music Video Agent PoC."""

from __future__ import annotations

import argparse
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

from break_records_agent.config import AgentConfig
from break_records_agent.overlays import generate_overlays
from break_records_agent.profiles import DemographicProfile, get_profile, list_profiles
from break_records_agent.video import compose_portrait_video
from break_records_agent.youtube import download_clips, search_clips


LOGGER = logging.getLogger("break_records_agent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a 1080x1920 short-form music promo video with AI text overlays."
    )
    parser.add_argument("--artist", help="Artist name to search for, e.g. 'SZA'.")
    parser.add_argument(
        "--profile",
        default="gen_z_rnb",
        help="Hardcoded demographic profile key. Use --list-profiles to view options.",
    )
    parser.add_argument("--age-range", help="Custom age range, e.g. '18-24'.")
    parser.add_argument(
        "--genres",
        help="Comma-separated custom genres. Overrides the selected profile when provided.",
    )
    parser.add_argument("--mood", help="Custom mood/vibe for overlay prompts.")
    parser.add_argument(
        "--search-limit",
        type=int,
        default=5,
        help="Number of YouTube results to inspect before downloading.",
    )
    parser.add_argument(
        "--clip-count",
        type=int,
        default=3,
        help="Number of successful clips to use in the final video.",
    )
    parser.add_argument(
        "--clip-seconds",
        type=float,
        default=10.0,
        help="Seconds to keep from each clip. Three 10s clips produce a 30s output.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where final MP4 files are written.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("work"),
        help="Directory for downloaded and rendered intermediate clips.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional exact output MP4 path. Defaults to output/<artist>_<timestamp>.mp4.",
    )
    parser.add_argument(
        "--mock-overlays",
        action="store_true",
        help="Use deterministic local overlays instead of calling Claude.",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="Print available hardcoded demographic profiles and exit.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def print_profiles() -> None:
    for profile in list_profiles():
        print(f"{profile.key}: {profile.label}")
        print(f"  Age: {profile.age_range}")
        print(f"  Genres: {', '.join(profile.genres)}")
        print(f"  Mood: {profile.mood}")


def build_profile(args: argparse.Namespace) -> DemographicProfile:
    base = get_profile(args.profile)
    if not any([args.age_range, args.genres, args.mood]):
        return base

    genres = tuple(
        item.strip()
        for item in (args.genres or ",".join(base.genres)).split(",")
        if item.strip()
    )
    return DemographicProfile(
        key="custom",
        label=f"Custom profile based on {base.label}",
        age_range=args.age_range or base.age_range,
        genres=genres,
        mood=args.mood or base.mood,
    )


def default_output_path(artist: str, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", artist.strip().lower()).strip("_")
    return output_dir / f"{slug or 'artist'}_{timestamp}.mp4"


def build_music_query(artist: str, profile: DemographicProfile) -> str:
    genre_terms = " ".join(profile.genres)
    return f"{artist} official music video live performance {genre_terms} {profile.mood}"


async def run_agent(args: argparse.Namespace) -> Path:
    if not args.artist:
        raise SystemExit("--artist is required unless --list-profiles is used.")

    profile = build_profile(args)
    output_path = args.output or default_output_path(args.artist, args.output_dir)
    config = AgentConfig(
        clip_count=args.clip_count,
        clip_seconds=args.clip_seconds,
        output_dir=args.output_dir,
        search_limit=args.search_limit,
        work_dir=args.work_dir,
    )

    query = build_music_query(args.artist, profile)
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
        artist=args.artist,
        profile=profile,
        clips=downloaded,
        mock=args.mock_overlays,
    )

    LOGGER.info("Composing final portrait MP4.")
    result_path = compose_portrait_video(
        clips=downloaded,
        overlays=overlays,
        output_path=output_path,
        render_dir=config.render_dir,
        clip_seconds=config.clip_seconds,
    )
    LOGGER.info("Finished: %s", result_path)
    return result_path


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    if args.list_profiles:
        print_profiles()
        return

    try:
        output_path = asyncio.run(run_agent(args))
    except KeyboardInterrupt:
        LOGGER.warning("Cancelled by user.")
        raise SystemExit(130)
    except Exception as exc:
        LOGGER.error("%s", exc)
        raise SystemExit(1)

    print(f"Created video: {output_path}")


if __name__ == "__main__":
    main()
