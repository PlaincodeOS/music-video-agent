# Break Records PoC - AI Music Video Agent

The AI Music Video Agent helps music artists and labels quickly create social-ready promotional clips. The MVP uses hardcoded audience profiles and YouTube as the clip source, while keeping the path open for Spotify API signals and additional media sources later.

The agent is designed around three priorities:

- Speed: generate a usable short-form video quickly.
- Cost efficiency: keep AI usage lightweight and predictable.
- Clean output quality: produce platform-ready MP4s for TikTok, Instagram Reels, and YouTube Shorts.

## MVP Scope

The first version should:

- Take an artist name and audience profile.
- Search YouTube for relevant music clips.
- Download short sections from usable clips.
- Generate short AI-written overlay text.
- Render clean white bottom-center text.
- Export a 1080x1920 H.264 MP4 between 15 and 30 seconds.

Spotify API integration, owned media libraries, and additional clip sources are planned future enhancements, not MVP requirements.

## Expected Input

- Artist name
- Audience age range
- Genres
- Mood or vibe
- Optional output path

## Expected Output

- MP4 file
- H.264 video with AAC audio
- 1080x1920 portrait format
- Duration between 15 and 30 seconds
- White text overlays at bottom center
- Preserved audio from source clips when available

## Workflow

1. Select a hardcoded demographic profile.
2. Search YouTube for relevant clips using `youtube-search-python`.
3. Download short clip sections with `yt-dlp`.
4. Generate one-line overlays with Claude Haiku.
5. Render overlays and compose the final MP4 with FFmpeg.

## Technical Direction

- Python 3.9+
- Claude Haiku API for overlay generation
- FFmpeg and `ffmpeg-python` for video processing
- `youtube-search-python` for search
- `yt-dlp` for downloads
- `asyncio` for orchestration

## Output Quality Rules

- Text must be clean white.
- Do not use shadows, outlines, boxes, or backgrounds behind text.
- Output must be exactly 1080x1920.
- Clip failures should be skipped instead of stopping the run.
- Final videos should feel ready for viral social platforms.

## Setup

Create and activate the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Set your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## Future Enhancements

- Spotify API integration for artist and audience insights
- Artist-owned content library support
- Additional video sources beyond YouTube
- Label-specific campaign templates
- Cloud upload and shareable links
- Performance feedback loops for better hooks and overlays
