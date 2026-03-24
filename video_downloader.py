#!/usr/bin/env python
"""
Nabbr - A simple wrapper for yt-dlp
This script provides an easy-to-use interface for downloading videos from various websites.
"""

import os
import sys
import subprocess
import shutil
import argparse
import glob
from pathlib import Path


# On Windows, prevent subprocess calls from spawning visible console windows
_subprocess_flags = {}
if sys.platform == 'win32':
    _subprocess_flags['creationflags'] = subprocess.CREATE_NO_WINDOW



def _find_deno():
    """Find the deno binary path (JS runtime required by yt-dlp for YouTube).
    Verifies the binary can actually execute (Windows Defender may block it)."""
    deno_name = 'deno.exe' if sys.platform == 'win32' else 'deno'
    candidates = []

    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        for d in [bundle_dir, os.path.dirname(sys.executable)]:
            p = os.path.join(d, deno_name)
            if os.path.exists(p):
                candidates.append(p)

    system_deno = shutil.which('deno')
    if system_deno:
        candidates.append(system_deno)

    # Homebrew fallback paths for macOS
    if sys.platform == 'darwin':
        for p in ['/opt/homebrew/bin/deno', '/usr/local/bin/deno']:
            if os.path.exists(p) and p not in candidates:
                candidates.append(p)

    # Verify each candidate can actually run (Defender may block bundled exe)
    for path in candidates:
        try:
            result = subprocess.run(
                [path, '--version'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=5, **_subprocess_flags,
            )
            if result.returncode == 0:
                print(f"Deno verified OK: {path}")
                return path
        except Exception as e:
            print(f"Deno at {path} failed verification: {e}")
            continue

    print("Warning: No working deno found — YouTube downloads may fail")
    return None


def _find_ffmpeg():
    """Find the FFmpeg binary path. Returns the path string or None if not found."""
    # When running as a PyInstaller bundle, check the extraction directory first
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        bundled = os.path.join(bundle_dir, 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
        if os.path.exists(bundled):
            return bundled
        # Also check next to the .exe itself (user may place ffmpeg beside Nabbr.exe)
        exe_dir = os.path.dirname(sys.executable)
        beside_exe = os.path.join(exe_dir, 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
        if os.path.exists(beside_exe):
            return beside_exe

    found = shutil.which("ffmpeg")
    if found:
        return found
    # Try common platform-specific locations as fallback
    if sys.platform == 'darwin':
        possible_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
        ]
    else:
        possible_paths = [
            "ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def convert_for_premiere(input_file, output_dir):
    """
    Convert a video file to be compatible with Adobe Premiere Pro using FFmpeg directly
    
    Args:
        input_file (str): Path to the input video file
        output_dir (str): Directory to save the converted file
    
    Returns:
        str: Path to the converted file or None if conversion failed
    """
    try:
        # Create output filename (same as original since we're replacing it)
        input_path = Path(input_file)
        output_filename = f"{input_path.stem}_premiere_temp.mp4"  # Temporary name to avoid conflict
        output_file = os.path.join(output_dir, output_filename)
        final_output_file = os.path.join(output_dir, f"{input_path.stem}.mp4")
        
        # Check if FFmpeg is available
        ffmpeg_cmd = _find_ffmpeg()
        if not ffmpeg_cmd:
            print("FFmpeg not found. Please install FFmpeg or add it to PATH.")
            return None

        # FFmpeg command for Premiere Pro compatibility
        # Preserve original quality and framerate - copy streams when possible
        command = [
            ffmpeg_cmd, "-y", "-i", input_file,
            # Video: Copy if already H.264, otherwise re-encode with original quality
            "-c:v", "libx264", "-crf", "18",  # Near-lossless quality
            "-preset", "slow",  # Better compression at same quality
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            # Audio: Keep original quality and sample rate
            "-c:a", "aac", "-q:a", "1",  # Highest AAC quality
            "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",
            output_file
        ]
        
        print(f"Converting video for Premiere Pro compatibility...")

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=3600, **_subprocess_flags)
        except subprocess.TimeoutExpired:
            print("FFmpeg conversion timed out after 1 hour")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None

        if result.returncode == 0:
            print(f"Conversion completed successfully!")

            # Replace original file with Premiere-optimized version (safe pattern)
            backup_file = input_file + ".bak"
            try:
                os.rename(input_file, backup_file)
                os.rename(output_file, final_output_file)
                print(f"Premiere-optimized file saved as: {os.path.basename(final_output_file)}")
                return final_output_file
            except Exception as e:
                print(f"Warning: Could not replace original file: {e}")
                if os.path.exists(backup_file) and not os.path.exists(input_file):
                    os.rename(backup_file, input_file)
                return output_file if os.path.exists(output_file) else None
            finally:
                # Clean up orphaned backup
                if os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except OSError:
                        pass
        else:
            print(f"Error during conversion: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception during conversion: {str(e)}")
        return None


def convert_for_davinci(input_file, output_dir):
    """
    Convert a video file to be compatible with DaVinci Resolve using FFmpeg
    
    Args:
        input_file (str): Path to the input video file
        output_dir (str): Directory to save the converted file
    
    Returns:
        str: Path to the converted file or None if conversion failed
    """
    try:
        # Create output filename (same as original since we're replacing it)
        input_path = Path(input_file)
        output_filename = f"{input_path.stem}_davinci_temp.mp4"  # Temporary name to avoid conflict
        output_file = os.path.join(output_dir, output_filename)
        final_output_file = os.path.join(output_dir, f"{input_path.stem}.mp4")
        
        # Check if FFmpeg is available
        ffmpeg_cmd = _find_ffmpeg()
        if not ffmpeg_cmd:
            print("FFmpeg not found. Please install FFmpeg or add it to PATH.")
            return None

        # FFmpeg command optimized for DaVinci Resolve compatibility
        # Preserve original quality while ensuring DaVinci compatibility
        command = [
            ffmpeg_cmd, "-y", "-i", input_file,
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-c:a", "aac", "-q:a", "1", "-ar", "48000", "-ac", "2",  # Highest quality audio
            "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",
            "-fflags", "+genpts",
            "-fps_mode", "cfr",  # Constant frame rate for timeline compatibility
            output_file
        ]
        
        print(f"Converting video for DaVinci Resolve compatibility...")

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=3600, **_subprocess_flags)
        except subprocess.TimeoutExpired:
            print("FFmpeg conversion timed out after 1 hour")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None

        if result.returncode == 0:
            print(f"DaVinci conversion completed successfully!")

            # Replace original file with DaVinci-optimized version (safe pattern)
            backup_file = input_file + ".bak"
            try:
                os.rename(input_file, backup_file)
                os.rename(output_file, final_output_file)
                print(f"DaVinci-optimized file saved as: {os.path.basename(final_output_file)}")
                return final_output_file
            except Exception as e:
                print(f"Warning: Could not replace original file: {e}")
                if os.path.exists(backup_file) and not os.path.exists(input_file):
                    os.rename(backup_file, input_file)
                return output_file if os.path.exists(output_file) else None
            finally:
                # Clean up orphaned backup
                if os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except OSError:
                        pass
        else:
            print(f"Error during DaVinci conversion: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception during DaVinci conversion: {str(e)}")
        return None


def download_video(url, output_path=None, video_format=None, audio_only=False, subtitle=False, quality=None, mp4=False, premiere=False, davinci=False, direct_convert=False, audio_quality="192", progress_hook=None, cookie_browser=None, remote_components=True):
    """
    Download video from URL with enhanced options and error handling

    Args:
        url (str): Video URL to download
        output_path (str): Directory to save the video
        video_format (str): Specific format to download
        audio_only (bool): Download audio only (MP3)
        subtitle (bool): Download subtitles if available
        quality (str): Video quality preference ('best', 'worst')
        mp4 (bool): Force MP4 format for video
        premiere (bool): Download format compatible with Adobe Premiere Pro
        davinci (bool): Download format compatible with DaVinci Resolve
        direct_convert (bool): Convert video using FFmpeg for guaranteed compatibility
        audio_quality (str): Audio quality for MP3 downloads
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Validate URL
    if not url or not url.strip():
        print("ERROR: Empty or None URL provided")
        return 1
    
    url = url.strip()
    if len(url) < 5:  # Minimum reasonable URL length
        print(f"ERROR: URL too short: '{url}'")
        return 1
    
    print(f"Starting download for URL: {url}")
    
    try:
        import yt_dlp

        supports_impersonate = False
        try:
            import curl_cffi  # Optional dependency for impersonation
            supports_impersonate = True
            print(f"curl_cffi loaded OK (version: {getattr(curl_cffi, '__version__', 'unknown')})")
        except Exception as e:
            print(f"curl_cffi not available: {e} — downloads will work but without browser impersonation")
            supports_impersonate = False

        # Set up yt-dlp options with minimal, proven configuration
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'noplaylist': True,
            'retries': 3,
            'fragment_retries': 3,
        }
        if supports_impersonate:
            try:
                from yt_dlp.networking.impersonate import ImpersonateTarget
                ydl_opts['impersonate'] = ImpersonateTarget.from_str('chrome')
                print("Chrome impersonation enabled")
            except Exception as e:
                print(f"Could not set up impersonation: {e}")
                supports_impersonate = False

        # Tell yt-dlp exactly where deno is (required for YouTube)
        deno_path = _find_deno()
        if deno_path:
            ydl_opts['js_runtimes'] = {'deno': {'path': deno_path}}
        else:
            # No deno available — still try, yt-dlp may work without JS for some videos
            # but YouTube will likely fail. Log prominently.
            print("ERROR: No working deno JS runtime found!")
            print("YouTube downloads require deno. Install from https://deno.land")

        # Tell yt-dlp where ffmpeg is
        ffmpeg_path = _find_ffmpeg()
        if ffmpeg_path:
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            ydl_opts['ffmpeg_location'] = ffmpeg_dir
            print(f"Using FFmpeg: {ffmpeg_path}")

        # Browser cookies — enables age-restricted and bot-detected video downloads
        if cookie_browser and cookie_browser.lower() != 'none':
            ydl_opts['cookiesfrombrowser'] = (cookie_browser.lower(), None, None, None)
            print(f"Browser cookies enabled: {cookie_browser}")

        # Remote challenge solvers — needed for YouTube JS challenges
        if remote_components:
            ydl_opts['remote_components'] = ['ejs:github']
            print("Remote challenge solvers enabled (ejs:github)")

        # Set output path
        if output_path:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            # Use forward slashes for yt-dlp compatibility
            sanitized_path = str(output_path).replace('\\', '/')
            ydl_opts['outtmpl'] = {'default': f"{sanitized_path}/%(title)s.%(ext)s"}
        
        # Handle audio-only downloads
        if audio_only:
            print(f"🎵 Downloading audio and converting to MP3 (Quality: {audio_quality}k)...")
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality,
            }]
        elif video_format:
            # Custom format specified
            ydl_opts['format'] = video_format
        else:
            # Video downloads - Quality and format selection
            # Strategy: always prefer H.264 (avc1) + AAC (m4a) so FFmpeg can
            # just mux into MP4 instantly (stream copy) instead of re-encoding.
            # VP9/WebM fallbacks are last resort — they require slow re-encoding.

            # H.264-first format string builder
            def _mp4_fmt(height_filter=''):
                """Build format string preferring H.264+AAC for instant MP4 mux."""
                hf = f'[height{height_filter}]' if height_filter else ''
                return (
                    # 1st: H.264 video + AAC audio (instant mux, no re-encode)
                    f'bestvideo{hf}[vcodec^=avc1]+bestaudio[acodec^=mp4a]/'
                    f'bestvideo{hf}[vcodec^=avc1]+bestaudio[ext=m4a]/'
                    # 2nd: Any MP4 container video + M4A audio
                    f'bestvideo{hf}[ext=mp4]+bestaudio[ext=m4a]/'
                    # 3rd: Best available (may need re-encode)
                    f'bestvideo{hf}+bestaudio/'
                    f'best'
                )

            need_mp4 = davinci or premiere or mp4

            if quality:
                if quality == "best":
                    if need_mp4:
                        ydl_opts['format'] = _mp4_fmt()
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                elif quality == "worst":
                    if need_mp4:
                        ydl_opts['format'] = (
                            'worstvideo[vcodec^=avc1]+worstaudio[ext=m4a]/'
                            'worstvideo[ext=mp4]+worstaudio[ext=m4a]/'
                            'worstvideo+worstaudio/worst'
                        )
                    else:
                        ydl_opts['format'] = 'worstvideo+worstaudio/worst'
            else:
                # Default: good quality balance
                if need_mp4:
                    ydl_opts['format'] = _mp4_fmt('<=1440')
                else:
                    ydl_opts['format'] = (
                        'bestvideo[height<=1440]+bestaudio/'
                        'bestvideo[height<=1080]+bestaudio/'
                        'bestvideo+bestaudio/best'
                    )

            if need_mp4:
                ydl_opts['merge_output_format'] = 'mp4'
                # Tell FFmpeg to copy streams when possible (no re-encoding)
                ydl_opts['postprocessor_args'] = {
                    'merger': ['-c', 'copy', '-movflags', '+faststart'],
                }
        
        # Subtitle options
        if subtitle:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['en', 'en-US', 'en-GB']
        
        print(f"📥 Starting download from: {url}")
        
        # Wire up progress reporting if a callback was provided
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]

        # Track existing files before download to detect new ones
        existing_files = set()
        if output_path and os.path.exists(output_path):
            all_extensions = ['*.mp4', '*.mkv', '*.webm', '*.mov', '*.avi', '*.flv', '*.mp3', '*.m4a', '*.aac', '*.opus', '*.wav']
            for ext in all_extensions:
                existing_files.update(glob.glob(f"{output_path}/{ext}"))
        
        # Download with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract info first
                print("🔍 Extracting video information...")
                info = ydl.extract_info(url, download=False)
                if info:
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    print(f"📹 Title: {title}")
                    if duration:
                        mins, secs = divmod(duration, 60)
                        print(f"⏱️ Duration: {mins:02d}:{secs:02d}")
                
                # Download the video
                print("📥 Starting download...")
                ydl.download([url])
                
                # Verify that NEW files were actually downloaded
                download_success = False
                new_files = []
                if output_path:
                    # Check for newly downloaded files (not existing ones)
                    all_extensions = ['*.mp4', '*.mkv', '*.webm', '*.mov', '*.avi', '*.flv', '*.mp3', '*.m4a', '*.aac', '*.opus', '*.wav']
                    current_files = set()
                    for ext in all_extensions:
                        current_files.update(glob.glob(f"{output_path}/{ext}"))

                    # Find files that are new (not in existing_files)
                    new_files = list(current_files - existing_files)
                    
                    if new_files:
                        download_success = True
                        print(f"📁 New files downloaded: {[os.path.basename(f) for f in new_files]}")
                    else:
                        print("❌ No new files detected - download likely failed")
                else:
                    # No output path specified, assume success (shouldn't happen in normal use)
                    download_success = True
                
                if download_success:
                    print("✅ SUCCESS: Download completed successfully!")
                    print(f"📁 File saved to: {output_path}")
                else:
                    print("❌ ERROR: Download completed but no NEW files were found!")
                    print("This suggests the download actually failed despite no exception being thrown.")
                    raise Exception("Download completed but no new output files were created")
                
                # Post-processing conversion if requested
                if direct_convert and output_path and download_success and new_files:
                    print("Starting post-download conversion...")

                    # Signal UI: conversion starting
                    if progress_hook:
                        progress_hook({'status': 'converting'})

                    # Use the newly downloaded files for conversion
                    files_to_convert = []
                    if audio_only:
                        audio_extensions = ['.mp3', '.m4a', '.aac', '.opus', '.wav']
                        files_to_convert = [f for f in new_files if any(f.lower().endswith(ext) for ext in audio_extensions)]
                    else:
                        video_extensions = ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv']
                        files_to_convert = [f for f in new_files if any(f.lower().endswith(ext) for ext in video_extensions)]

                    converted_file = None
                    if files_to_convert:
                        latest_file = files_to_convert[0]

                        if davinci:
                            print("Converting for DaVinci Resolve compatibility...")
                            converted_file = convert_for_davinci(latest_file, output_path)
                            if converted_file:
                                print(f"DaVinci-compatible file created: {os.path.basename(converted_file)}")
                        elif premiere:
                            print("Converting for Premiere Pro compatibility...")
                            converted_file = convert_for_premiere(latest_file, output_path)
                            if converted_file:
                                print(f"Premiere-compatible file created: {os.path.basename(converted_file)}")
                    else:
                        print("Warning: Could not find downloaded file for conversion")

                    # Signal UI: conversion done
                    if progress_hook:
                        progress_hook({'status': 'convert_done'})
                
                return 0
                
            except Exception as e:
                import traceback
                error_msg = str(e) or repr(e)
                print(f"❌ Download error: {error_msg}")
                print(f"❌ Download traceback:\n{traceback.format_exc()}")
                
                # Try fallback method for DNS issues or player response failures
                if ('Failed to resolve' in error_msg or 'getaddrinfo failed' in error_msg or 
                    'Failed to extract any player response' in error_msg or 
                    'Unable to download API page' in error_msg):
                    
                    print("🔄 Trying simplified fallback methods...")
                    
                    # Use simple fallback strategies that are more likely to work
                    fallback_strategies = [
                        # Strategy 1: Worst quality (fastest and most reliable)
                        {
                            'name': 'Worst Quality Fallback',
                            'format': 'worst',
                        },
                        # Strategy 2: Force different format selection
                        {
                            'name': 'Format 18 (360p mp4)',
                            'format': '18',  # This is a very common, reliable format
                        },
                        # Strategy 3: Audio only fallback
                        {
                            'name': 'Audio Only Fallback',
                            'format': 'bestaudio',
                        }
                    ]
                    
                    for strategy in fallback_strategies:
                        try:
                            print(f"🔄 Trying {strategy['name']} extraction...")
                            fallback_opts = ydl_opts.copy()
                            # Apply the format override for this strategy
                            fallback_opts['format'] = strategy['format']
                            
                            with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                                fallback_ydl.download([url])
                                
                                # Verify that NEW files were downloaded for fallback too
                                fallback_success = False
                                if output_path:
                                    all_extensions = ['*.mp4', '*.mkv', '*.webm', '*.mov', '*.avi', '*.flv', '*.mp3', '*.m4a', '*.aac', '*.opus', '*.wav']
                                    current_files = set()
                                    for ext in all_extensions:
                                        current_files.update(glob.glob(f"{output_path}/{ext}"))
                                    
                                    # Find files that are new (not in existing_files from before)
                                    new_fallback_files = list(current_files - existing_files)
                                    
                                    if new_fallback_files:
                                        fallback_success = True
                                        print(f"📁 New files downloaded by {strategy['name']}: {[os.path.basename(f) for f in new_fallback_files]}")
                                    else:
                                        print(f"❌ {strategy['name']} completed but no new files found")
                                else:
                                    fallback_success = True
                                
                                if fallback_success:
                                    print(f"✅ SUCCESS: {strategy['name']} download completed successfully!")
                                    print(f"📁 File saved to: {output_path}")
                                    return 0
                                else:
                                    continue
                                
                        except Exception as fallback_e:
                            print(f"❌ {strategy['name']} failed: {str(fallback_e)[:100]}...")
                            continue
                    
                    print("❌ All fallback methods failed")
                    return 1  # Return error code when all fallbacks fail
                
                # Handle common errors with suggested solutions
                if 'age-restricted' in error_msg.lower() or 'sign in to confirm' in error_msg.lower():
                    if 'bot' in error_msg.lower():
                        print("BOT DETECTION: YouTube thinks this is automated.")
                        print("   Fix: Go to the Advanced tab and select your browser under 'Browser Cookies'.")
                    else:
                        print("AGE-RESTRICTED VIDEO: This video requires authentication.")
                        print("   Fix: Go to the Advanced tab and select your browser under 'Browser Cookies'.")
                elif 'private video' in error_msg.lower():
                    print("💡 Suggestion: This video is private. Check if you have access or if the URL is correct.")
                elif 'not available' in error_msg.lower():
                    print("💡 Suggestion: Video may be geo-restricted or temporarily unavailable.")
                elif 'format' in error_msg.lower():
                    print("💡 Suggestion: Try a different quality setting or enable MP4 format.")
                elif 'failed to resolve' in error_msg.lower() or 'player response' in error_msg.lower():
                    print("💡 Suggestion: This appears to be a YouTube API/network issue. Try:")
                    print("   - Updating yt-dlp: pip install --upgrade yt-dlp")
                    print("   - Checking your internet connection")
                    print("   - Using a VPN if you're in a restricted region")
                    print("   - Trying a different YouTube URL to test")
                    print("   - Clearing browser cache and cookies")
                
                return 1
                
    except ImportError as e:
        print(f"❌ Error: yt-dlp is not installed or failed to import: {e}")
        return 1
    except SystemExit as e:
        import traceback
        print(f"❌ yt-dlp called sys.exit({e.code})")
        print(f"❌ Traceback:\n{traceback.format_exc()}")
        return 1
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error: {repr(e)}")
        print(f"❌ Traceback:\n{traceback.format_exc()}")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Download videos from the web using yt-dlp")
    parser.add_argument("url", help="URL of the video to download")
    parser.add_argument("-o", "--output", help="Output directory path")
    parser.add_argument("-f", "--format", help="Specific format to download")
    parser.add_argument("-a", "--audio", action="store_true", help="Download audio only")
    parser.add_argument("-s", "--subtitle", action="store_true", help="Download subtitles if available")
    parser.add_argument("-q", "--quality", choices=["best", "worst"], help="Video quality")
    parser.add_argument("--mp4", action="store_true", help="Force MP4 format")
    parser.add_argument("--premiere", action="store_true", help="Format compatible with Adobe Premiere Pro")
    parser.add_argument("--davinci", action="store_true", help="Format compatible with DaVinci Resolve")
    parser.add_argument("--convert", action="store_true", help="Convert downloaded video with FFmpeg for guaranteed compatibility")
    parser.add_argument("--convert-file", help="Convert an existing video file for editing software compatibility")
    parser.add_argument("--convert-type", choices=["premiere", "davinci"], default="premiere", help="Type of conversion for --convert-file")
    parser.add_argument("--audio-quality", default="192", help="Audio quality for MP3 conversion (default: 192k)")
    
    args = parser.parse_args()
    
    # If convert-file is specified, just convert an existing file
    if args.convert_file:
        if not args.output:
            output_dir = os.path.dirname(args.convert_file)
        else:
            output_dir = args.output
        
        if args.convert_type == "davinci":
            print("🎬 Converting for DaVinci Resolve...")
            convert_for_davinci(args.convert_file, output_dir)
        else:
            print("🎬 Converting for Premiere Pro...")
            convert_for_premiere(args.convert_file, output_dir)
    else:
        # Normal download operation
        exit_code = download_video(
            args.url,
            output_path=args.output,
            video_format=args.format,
            audio_only=args.audio,
            subtitle=args.subtitle,
            quality=args.quality,
            mp4=args.mp4,
            premiere=args.premiere,
            davinci=args.davinci,
            direct_convert=args.convert,
            audio_quality=args.audio_quality
        )
        
        if exit_code == 0:
            print("\n🎉 All operations completed successfully!")
        else:
            print(f"\n❌ Operation failed with exit code: {exit_code}")
            sys.exit(exit_code)

if __name__ == "__main__":
    main()
