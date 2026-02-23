<p align="center">
  <img src="app_icon.png" alt="Nabbr logo" width="140">
</p>

<h1 align="center">Nabbr</h1>

<p align="center">Snag, sort, and prep your own videos with raccoon-level focus.</p>

<p align="center">
  <a href="LICENSE"><img alt="License: GPL-3.0" src="https://img.shields.io/badge/License-GPLv3-blue.svg"></a>
  <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="Windows and macOS" src="https://img.shields.io/badge/OS-Windows%20%7C%20macOS-0078D6?logo=windows&logoColor=white">
  <img alt="Backend: yt-dlp" src="https://img.shields.io/badge/Backend-yt--dlp-2ea44f">
</p>

## What is Nabbr?

Your friendly neighborhood video raccoon. Nabbr is a desktop app for collecting and converting videos and audio you own or are authorized to process, then packaging them into editor-ready formats with a tidy, modern UI.

## Features

- ?? Friendly desktop UI powered by PyQt5
- ?? Video or audio downloads with batch queues
- ?? One-click editor presets for Premiere Pro and DaVinci Resolve
- ?? FFmpeg-powered conversions with sensible defaults
- ?? Remembers folders, window size, and preferences

## Quick Start

```bash
git clone https://github.com/your-org/nabbr.git
cd nabbr
pip install -r requirements.txt
python video_downloader_ui.py
```

## FFmpeg Install

<details>
<summary>Install FFmpeg (required for conversions)</summary>

- Windows: download from https://ffmpeg.org/download.html, unzip, and add the `bin` folder to your PATH.
- macOS: install via Homebrew with `brew install ffmpeg`.

</details>

## Editor Presets

| Editor | Video | Audio | Notes |
| --- | --- | --- | --- |
| Premiere Pro | H.264 High, CRF 18 | AAC 192k, 48kHz | FastStart, yuv420p |
| DaVinci Resolve | H.264 4.1, CRF 18 | AAC 320k, 48kHz stereo | BT.709, CFR, genpts |

## Build from Source

```bash
python build_app.py
```

## How It Works

1. GUI collects URLs and settings.
2. Backend (yt-dlp) fetches the authorized media.
3. FFmpeg converts to the selected editor preset.

> [!CAUTION]
> Legal disclaimer: Nabbr is provided for lawful use only. You are responsible for ensuring you own the content or have explicit authorization to process it and for complying with all applicable laws and platform terms. Do not use Nabbr to access or process content you do not have rights to.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- [FFmpeg](https://ffmpeg.org/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)

## License

Nabbr is licensed under GPL-3.0. See [LICENSE](LICENSE).

| Dependency | License | Notes |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense | Backend downloader |
| [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0-or-later / Commercial | GUI framework |
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1-or-later / GPL-2.0-or-later (build-dependent) | Media processing |
| [curl_cffi](https://github.com/yifeikong/curl_cffi) | MIT | Network layer |

---

Made with raccoon energy.
