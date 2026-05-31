"""CLI entry point for the Break Records AI Music Video Agent PoC."""

from __future__ import annotations

import argparse
import logging

from break_records_agent.profiles import list_profiles
from break_records_agent.runner import RunRequest, run_generation_sync


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
        "--drive-folder-id",
        help="Optional Google Drive folder ID for the uploaded MP4.",
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


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    if args.list_profiles:
        print_profiles()
        return

    if not args.artist:
        raise SystemExit("--artist is required unless --list-profiles is used.")

    request = RunRequest(
        artist=args.artist,
        profile_key=args.profile,
        age_range=args.age_range,
        genres=(item.strip() for item in (args.genres or "").split(",") if item.strip())
        if args.genres
        else None,
        mood=args.mood,
        search_limit=args.search_limit,
        clip_count=args.clip_count,
        clip_seconds=args.clip_seconds,
        mock_overlays=args.mock_overlays,
        drive_folder_id=args.drive_folder_id,
    )

    try:
        result = run_generation_sync(request)
    except KeyboardInterrupt:
        LOGGER.warning("Cancelled by user.")
        raise SystemExit(130)
    except Exception as exc:
        LOGGER.error("%s", exc)
        raise SystemExit(1)

    print("Uploaded video to Google Drive:")
    print(f"  File ID: {result.file_id}")
    if result.web_view_link:
        print(f"  View Link: {result.web_view_link}")
    if result.web_content_link:
        print(f"  Download Link: {result.web_content_link}")


if __name__ == "__main__":
    main()
