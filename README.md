# Break Records PoC - AI Music Video Agent (Django)

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
- Upload the final MP4 to Google Drive instead of writing to a local output directory.

Spotify API integration, owned media libraries, and additional clip sources are planned future enhancements, not MVP requirements.

## Expected Input

- Artist name
- Audience age range
- Genres
- Mood or vibe
- Optional Google Drive folder ID

## Expected Output

- MP4 file uploaded to Google Drive
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
6. Upload the final MP4 to Google Drive and clean up temporary files.

## Technical Direction

- Python 3.9+
- Claude Haiku API for overlay generation
- FFmpeg and `ffmpeg-python` for video processing
- Django API for hosting
- Google Drive API for uploads
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

# Django settings
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=*

# Google Drive upload settings
# Option A (recommended for Render secrets):
# Paste the entire service account JSON as a single line string.
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
# Option B: base64-encoded service account JSON
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=base64-encoded-json
# Option C (local dev): path to your service account JSON key
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
# Optional folder ID to upload videos into
GDRIVE_FOLDER_ID=
# Optional shared drive ID (required for service accounts without storage quota)
GDRIVE_SHARED_DRIVE_ID=
# Set true to make uploaded videos public
GDRIVE_PUBLIC=false
```

## Running the Django API

Start the Django server:

```bash
python manage.py runserver
```

Open the web UI at `/api/` to submit video generation requests from a form.

Send a POST request to `/api/generate/` with JSON similar to:

```json
{
	"artist": "SZA",
	"profile": "gen_z_rnb",
	"clip_count": 3,
	"clip_seconds": 10,
	"mock_overlays": false,
	"drive_folder_id": "optional-folder-id"
}
```

The response includes a Google Drive `file_id` and share links if available.

## Future Enhancements

- Spotify API integration for artist and audience insights
- Artist-owned content library support
- Additional video sources beyond YouTube
- Label-specific campaign templates
- Cloud upload and shareable links
- Performance feedback loops for better hooks and overlays
