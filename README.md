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

---

## What is Nabbr?

A desktop app for downloading and converting videos and audio you own or are authorized to use. Supports YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo, and [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) via yt-dlp. Packages downloads into editor-ready formats with a clean, modern UI.

## Download

**[Download Nabbr.exe from GitHub Releases](https://github.com/LuisFaxas/nabbr/releases/latest)**

Double-click to run. No install required. Fully portable — works from any folder.

> FFmpeg and Deno are bundled inside the .exe. Everything you need is included.

---

## Features

### Core
- Video downloads with quality selection (best / worst / auto)
- Audio extraction to MP3 (192k / 128k / 96k bitrate)
- Batch download queues — add multiple URLs, download them all
- Subtitle downloads (when available)

### Editor Integration
- One-click **Premiere Pro** preset (H.264 High + AAC, FastStart)
- One-click **DaVinci Resolve** preset (H.264 4.1, BT.709, CFR, 48kHz stereo)
- Prefers H.264 + AAC streams for instant MP4 mux (no slow re-encoding)

### YouTube Reliability
- **Browser cookie support** — unlocks age-restricted and bot-detected videos
- **Chrome impersonation** via curl_cffi — bypasses bot detection
- **Remote challenge solvers** — downloads small JS scripts to solve YouTube challenges (sandboxed, no network access)
- **Deno JS runtime** bundled — required by yt-dlp for YouTube extraction

### Privacy & Settings
- Persistent settings, recent directories, and download history
- No telemetry, no analytics — zero data leaves your machine
- URLs redacted from log files
- Download history stores domains only, never full URLs

---

## How It Works

1. **You enter a URL** and pick your options (quality, format, editor preset).
2. **yt-dlp fetches the media**, preferring H.264 + AAC streams so FFmpeg can mux instantly without re-encoding.
3. **FFmpeg converts** to your selected editor preset (if enabled), producing a file that drops straight into your timeline.

---

## Editor Presets

| Editor | Video | Audio | Extras |
| --- | --- | --- | --- |
| **Premiere Pro** | H.264 High, CRF 18, yuv420p | AAC VBR quality 1 | FastStart, zero-offset timestamps |
| **DaVinci Resolve** | H.264 4.1, CRF 18, BT.709 color | AAC VBR quality 1, 48kHz stereo | CFR, genpts, FastStart |

Both presets produce near-lossless quality. CRF 18 preserves detail while keeping file sizes reasonable.

---

## Browser Cookies

Some videos require authentication — age-restricted content, bot-detected requests, or private videos you have access to.

**How to enable:**
1. Go to the **Advanced** tab in Nabbr
2. Under **Browser Cookies**, select your browser (Chrome, Edge, Firefox, or Brave)
3. Download normally — Nabbr reads your browser's cookies to authenticate

**Important:**
- Cookies are read **in-memory only** and discarded after the download
- Nabbr **never saves, exports, or transmits** your cookies
- Your browser does **not** need to be closed (works while browsing)

---

## Security & Privacy

Nabbr is designed to be safe and transparent.

| Practice | Detail |
| --- | --- |
| **No telemetry** | Zero network calls besides the video download itself |
| **Local settings** | Everything stored at `~/.nabbr/settings.json` on your machine |
| **Domain-only history** | Download history stores `youtube.com`, not the full URL |
| **Log redaction** | URLs are stripped from log files automatically |
| **Log rotation** | Logs capped at 5 MB with 3 backups — won't fill your disk |
| **File permissions** | Settings file restricted to owner-only on Unix (0600) |
| **Safe imports** | Settings import validates keys and types — rejects unknown fields |
| **No shell injection** | All subprocess calls use list-based arguments, never `shell=True` |
| **Path validation** | Download paths are checked against system directories |
| **Conversion timeout** | FFmpeg conversions have a 1-hour timeout to prevent hangs |
| **Cookie handling** | Browser cookies read in-memory, never persisted or transmitted |

---

## Quick Start (from source)

### Prerequisites
- Python 3.11+
- pip

### Install and run

```bash
git clone https://github.com/LuisFaxas/nabbr.git
cd nabbr
pip install -r requirements.txt
python video_downloader_ui.py
```

### Build a standalone executable

```bash
pip install pyinstaller
python build_app.py
# Output: dist/Nabbr.exe (Windows) or dist/Nabbr.app (macOS)
```

To bundle FFmpeg and Deno into the .exe, place `ffmpeg.exe` and `deno.exe` in the project directory before building.

---

## FFmpeg Install

<details>
<summary>Click to expand — only needed when running from source</summary>

FFmpeg is required for editor conversions (Premiere Pro / DaVinci Resolve presets) and audio extraction.

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or [BtbN builds](https://github.com/BtbN/FFmpeg-Builds/releases). Extract and add the `bin` folder to your PATH, or place `ffmpeg.exe` next to `video_downloader_ui.py`.
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` or equivalent

The pre-built .exe from Releases already includes FFmpeg — no separate install needed.

</details>

---

## Troubleshooting

| Error | Fix |
| --- | --- |
| **"Sign in to confirm your age"** | Go to Advanced tab → Browser Cookies → select your browser |
| **"Sign in to confirm you're not a bot"** | Same as above. Also ensure "Allow remote challenge solvers" is checked |
| **"No supported JavaScript runtime"** | Deno is missing. Install from [deno.land](https://deno.land) (or use the pre-built .exe which bundles it) |
| **Download is slow / file keeps growing** | VP9 video is being re-encoded to H.264. This is normal for some formats. Nabbr automatically prefers H.264 streams to avoid this |
| **"FFmpeg not found"** | Install FFmpeg (see above) or use the pre-built .exe |
| **App crashes silently** | Check logs at `~/.nabbr/nabbr.log` (Windows: `C:\Users\<you>\.nabbr\nabbr.log`) |

---

## Legal Notice

> **Nabbr is provided for lawful use only.**

### Your Responsibilities

1. **Content rights.** You must own the content you download, or have explicit permission from the rights holder. This includes respecting copyright, trademark, and intellectual property laws.

2. **Terms of service.** Many platforms (YouTube, TikTok, Instagram, etc.) prohibit downloading content in their Terms of Service. You are responsible for understanding and complying with these terms.

3. **Fair use is not a blanket protection.** Downloading copyrighted content may be defensible under fair use (commentary, criticism, education, research, parody), but fair use is determined on a **case-by-case basis** by courts. Simply claiming "fair use" or "no infringement intended" does not make it so.

4. **Laws vary by jurisdiction.** Copyright and circumvention laws differ between countries:
   - **United States**: DMCA Section 1201 prohibits circumventing technological protection measures, with limited fair use exceptions.
   - **European Union**: The Copyright Directive (Article 6) has similar restrictions, with member-state variations.
   - **Other regions**: Check your local laws. There is no internationally uniform standard.

5. **Do not use Nabbr for piracy.** Do not download, redistribute, or commercially exploit content you do not have rights to.

### Our Limitations

- Nabbr is provided **"as-is" without warranty of any kind** (see [LICENSE](LICENSE) for full GPL-3.0 terms).
- The developers assume **no liability** for how you use downloaded content or for any copyright claims that arise from your use.
- Nabbr is a general-purpose tool. Like a web browser or a file manager, it has legitimate uses. **The responsibility for lawful use rests entirely with you.**

### Privacy & Cookie Notice

- Nabbr may read cookies from your browser to authenticate with video sources (e.g., for age-restricted content you have access to).
- Cookies are read from your browser's **local storage on your machine**.
- Cookies are held **in memory only** during the download and are **never saved, exported, or transmitted** to any third party.
- Nabbr collects **no analytics, no telemetry, and no usage data**. Nothing leaves your machine except the download request to the video source.

### Indemnification

By using Nabbr, you agree to indemnify and hold harmless the developers, maintainers, and contributors from any claims, damages, losses, or legal action arising from your use of the software or the content you download.

### Disclaimer of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING BUT NOT LIMITED TO PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — the backend that makes it all work
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — desktop UI framework
- [FFmpeg](https://ffmpeg.org/) — media processing engine
- [curl_cffi](https://github.com/yifeikong/curl_cffi) — browser impersonation layer
- [Deno](https://deno.land/) — JavaScript runtime for YouTube challenge solving

## License

Nabbr is licensed under **GPL-3.0**. See [LICENSE](LICENSE).

| Dependency | License | Role |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense | Backend downloader |
| [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0-or-later / Commercial | GUI framework |
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1+ / GPL-2.0+ (build-dependent) | Media processing |
| [curl_cffi](https://github.com/yifeikong/curl_cffi) | MIT | Network layer |
| [Deno](https://deno.land/) | MIT | JS runtime |

---

<p align="center">Made with raccoon energy.</p>
