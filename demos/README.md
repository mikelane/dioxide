# Dioxide Demo Videos

This directory contains the GitHub Pages demo site for dioxide's narrated terminal recordings.

**Live site:** [mikelane.github.io/dioxide/](https://mikelane.github.io/dioxide/)

## Overview

Each demo is a narrated terminal recording that showcases a specific capability of dioxide. The demos are:

| # | Demo | Issue | Status |
|---|------|-------|--------|
| 1 | Before/After Scan Performance | [#385](https://github.com/mikelane/dioxide/issues/385) | Planned |
| 2 | Side-by-Side Decorator Usage | [#389](https://github.com/mikelane/dioxide/issues/389) | Planned |
| 3 | Rust Backend Correctness Guarantees | [#393](https://github.com/mikelane/dioxide/issues/393) | Planned |
| 4 | Mock-to-Fake Migration | [#404](https://github.com/mikelane/dioxide/issues/404) | Planned |
| 5 | Automated Migration Tool | [#410](https://github.com/mikelane/dioxide/issues/410) | Planned |

## Why Not Git LFS?

GitHub Pages does **not** serve Git LFS objects. Pages deployments download files from the repository, but LFS replaces large files with pointer files. The result: visitors would download a small text pointer instead of the actual video.

Instead, MP4 files are committed directly to the repository. Each demo video is expected to be 5-20MB, well within GitHub's 100MB per-file limit.

## Recording Pipeline

The full pipeline for creating a demo video is:

```
Write script --> Record terminal --> Convert to MP4 --> Generate narration --> Combine --> Commit
```

### Prerequisites

Install the required tools:

```bash
# Terminal recording
brew install asciinema

# GIF/MP4 conversion (asciinema gif generator)
cargo install agg

# Video/audio processing
brew install ffmpeg
```

### Step 1: Write the Demo Script

Create a demo script in `narration-scripts/` based on the template:

```bash
cp narration-scripts/template.md narration-scripts/demo-name.md
```

The script should include:
- **Commands to run** with expected output
- **Narration text** with timing markers (timestamps relative to recording start)
- **Pause points** where the narrator explains what happened

See `narration-scripts/template.md` for the full format.

### Step 2: Record the Terminal Session

Use the recording helper script or record manually:

```bash
# Using the helper script
./scripts/record-demo.sh demo-name

# Manual recording
asciinema rec --cols 120 --rows 35 --idle-time-limit 2 recordings/demo-name.cast
```

Recording conventions:
- **Terminal size:** 120 columns x 35 rows
- **Font:** JetBrains Mono or system monospace
- **Color theme:** Dracula (consistent across all demos)
- **Idle limit:** 2 seconds (long pauses are trimmed automatically)
- **Shell prompt:** Keep it simple (e.g., `$ `)

Preview your recording:

```bash
asciinema play recordings/demo-name.cast
```

### Step 3: Convert to MP4

Convert the `.cast` file to an animated GIF, then to MP4:

```bash
# Cast to GIF
agg --font-family "JetBrains Mono" \
    --theme dracula \
    --cols 120 --rows 35 \
    recordings/demo-name.cast \
    recordings/demo-name.gif

# GIF to MP4 (H.264 for browser compatibility)
ffmpeg -i recordings/demo-name.gif \
    -movflags faststart \
    -pix_fmt yuv420p \
    -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    recordings/demo-name.mp4
```

### Step 4: Generate Narration Audio

Use the ElevenLabs API to generate voiceover from your narration script:

```bash
# Set API credentials (never commit these)
export ELEVENLABS_API_KEY="your-api-key"
export ELEVENLABS_VOICE_ID="your-voice-id"

# Generate narration
python scripts/generate-narration.py \
    narration-scripts/demo-name.md \
    recordings/demo-name-narration.mp3
```

### Step 5: Combine Video and Audio

Overlay the narration audio onto the terminal recording:

```bash
./scripts/combine-video-audio.sh \
    recordings/demo-name.mp4 \
    recordings/demo-name-narration.mp3 \
    videos/demo-name.mp4
```

This uses ffmpeg to:
- Keep the video stream as-is
- Encode the audio as AAC
- Pad the shorter stream so video and audio lengths match

### Step 6: Commit and Deploy

```bash
# Add the final video
git add videos/demo-name.mp4

# Commit
git commit -m "feat: add demo-name demo video (#ISSUE)"

# Push to main (triggers GitHub Pages deployment)
git push origin main
```

## Directory Structure

```
demos/
├── README.md                    # This file
├── index.html                   # Landing page (all demos)
├── demo.html                    # Template for individual demo pages
├── videos/                      # Final MP4 files (committed directly, not LFS)
│   └── .gitkeep
├── scripts/                     # Pipeline automation scripts
│   ├── record-demo.sh           # Terminal recording helper
│   ├── generate-narration.py    # ElevenLabs narration generator
│   └── combine-video-audio.sh   # ffmpeg video+audio combiner
└── narration-scripts/           # Narration text with timing markers
    └── template.md              # Template for new narration scripts
```

## Site Structure

The demo site is deployed to GitHub Pages via the `deploy-demos.yml` workflow. It triggers automatically when files in the `demos/` directory change on the `main` branch.

The site uses plain HTML with inline CSS. No build tools, JavaScript frameworks, or external dependencies are required.

## Updating the Site

To add a new demo:

1. Follow the recording pipeline above to create the video
2. Copy `demo.html` to a new file (e.g., `scan-performance.html`)
3. Replace the template placeholders (DEMO_TITLE, DEMO_VIDEO_FILE, etc.)
4. Update `index.html` to link to the new page and change its badge from "Coming Soon" to "Ready"
5. Commit all changes and push to `main`
