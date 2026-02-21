# Nabbr

A desktop app for downloading videos and audio from YouTube, TikTok, Instagram, and 1000+ sites. Built with PyQt5 and yt-dlp, with automatic format conversion for Adobe Premiere Pro and DaVinci Resolve.

## Features

- **Multi-platform**: YouTube, TikTok, Instagram, Twitter/X, Facebook, Vimeo, and [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- **Video & audio**: Download full video (MP4) or extract audio (MP3)
- **Editor-ready**: One-click conversion for Premiere Pro and DaVinci Resolve
- **Batch downloads**: Queue multiple URLs for sequential downloading
- **Smart settings**: Remembers directories, window size, and preferences

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python video_downloader_ui.py
```

FFmpeg is required for video conversion. Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system PATH.

## Command Line

```bash
# Download video for Premiere Pro
python video_downloader.py "https://youtube.com/watch?v=example" --premiere --convert

# Download audio only
python video_downloader.py "https://youtube.com/watch?v=example" --audio --audio-quality 320

# Convert existing file for DaVinci Resolve
python video_downloader.py --convert-file "video.mp4" --convert-type davinci
```

Run `python video_downloader.py --help` for all options.

## Editor Presets

| Editor | Codec | Audio | Extras |
|--------|-------|-------|--------|
| **Premiere Pro** | H.264 High, CRF 18 | AAC 192k, 48kHz | FastStart, yuv420p |
| **DaVinci Resolve** | H.264 4.1, CRF 18 | AAC 320k, 48kHz stereo | BT.709, CFR, genpts |

## Build Executable

```bash
python build_app.py
```

Creates `dist/Nabbr.exe` (Windows). Optionally place `ffmpeg.exe` in the project root before building to bundle it.

## Requirements

- Python 3.7+
- PyQt5
- yt-dlp
- curl_cffi
- FFmpeg (external binary)

## Disclaimer

Nabbr is a tool for downloading media you have the right to access. Users are responsible for complying with applicable laws and the terms of service of any platform they download from. The authors do not condone or encourage downloading copyrighted content without permission.

## License

MIT License. See [LICENSE](LICENSE) for details.
