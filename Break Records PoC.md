# Break Records PoC - AI Video Agent

The AI Music Video Agent will serve as a content generation tool for music artists and labels, enabling quick creation of social-ready video clips for marketing and promotion. 

The MVP focuses on hardcoded profiles and YouTube as the clip source, with plans to integrate Spotify API and additional clip sources later. 

The agent should prioritize speed, cost efficiency, and clean output quality suitable for viral social platforms.

Build an AI agent that takes an artist name and audience demographic, finds relevant video clips, generates AI-written text overlays, and outputs a ready-to-post MP4 video (1080x1920 portrait, 15-30 seconds).

## Input
- Artist name
- Age range
- Genres
- Mood/vibe

## Output
- MP4 file (H.264, 1080x1920 portrait)
- Duration: 15-30 seconds
- White text overlays at bottom center
- Audio preserved from clips

## The 4-Step Workflow

### Step 1: Input Demographics
Hardcode 3-5 demographic profiles for the PoC. No Spotify API needed yet.

### Step 2: Find & Download Clips
Search YouTube for 4-5 relevant clips using youtube-search-python. Download each clip (10-15 seconds) with yt-dlp. Skip clips that fail to download, don't error out.

### Step 3: Generate Text Overlays
For each clip, call Claude Haiku API with a prompt like: "Write a 1-line text overlay for [age] year olds who like [genres]. Clip: [title]. Vibe: [mood]. Max 8 words." Use async calls to speed this up.

### Step 4: Compose Video
Load clips with their text, render white text (Arial Bold, 48-56px, no shadows or backgrounds) at bottom center using FFmpeg's drawtext filter. Concatenate with hard cuts, preserve audio, export as MP4.

## Tech Stack
- Language: Python 3.9+
- AI: Claude Haiku API
- Video: FFmpeg (ffmpeg-python)
- Search: youtube-search-python
- Download: yt-dlp
- Orchestration: asyncio

## Key Requirements
- Text must be clean white with no shadows, outlines, or backgrounds
- Video must be exactly 1080x1920 (portrait)
- Execution time: under 2 minutes per video
- Cost: under $0.001 per video

## Deliverables
- video_agent.py script
- Hardcoded demographic profiles (3-5 examples)
- MP4 output (clean text, correct aspect ratio)
- Error handling and logging
- README with setup and usage
- Sample output video
- requirements.txt

## Success Criteria
- Script runs without errors from CLI
- Text is clean and readable (no distortion)
- Output is exactly 1080x1920
- Duration is 15-30 seconds
- Ready to post on TikTok, Instagram Reels, YouTube Shorts
- Execution under 2 minutes
- Cost under $0.001 per video

## Quick Decisions
- Use youtube-search-python (free, no API key)
- Skip failed clips, don't error out entirely
- Preserve audio from all clips
- Store locally for MVP, add cloud upload later if needed

## Important Notes
Text rendering is critical: must be clean white with no backgrounds or shadows. Use FFmpeg drawtext with no box option. Portrait video (1080x1920) is non-standard, so ensure clips are scaled/cropped properly. Execution bottleneck will likely be video download time.
