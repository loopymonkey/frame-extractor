# Video Frame Extractor (macOS)

Desktop app built with Flet and OpenCV to extract the first frame of video files and save as JPG.

## Features

- Select multiple video files
- Optional max width / max height constraints
- Aspect ratio preserved automatically
- Default output folder: `RESIZED` next to each source video
- Optional custom output folder override
- Duplicate-safe output naming (`*_first_frame.jpg`, `*_first_frame_1.jpg`, etc.)

## Requirements

- Python 3.12 recommended
- macOS (Apple Silicon build example below uses `arm64`)

## Setup

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
```

## Run Locally

```bash
source .venv312/bin/activate
python main.py
```

## Build macOS App

```bash
source .venv312/bin/activate
flet build macos . --arch arm64
```

The `.app` bundle is created in `build/macos/`.
