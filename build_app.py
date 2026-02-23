#!/usr/bin/env python
"""
Build Script for Nabbr
Creates a standalone executable using PyInstaller.
Supports both Windows and macOS.
"""

import os
import shutil
import subprocess
import sys


def build_executable():
    """Build a standalone executable for Nabbr."""

    is_mac = sys.platform == 'darwin'
    path_sep = ':' if is_mac else ';'
    app_name = 'Nabbr.app' if is_mac else 'Nabbr.exe'

    print(f"Building Nabbr for {'macOS' if is_mac else 'Windows'}...")

    # Clean previous build directories if they exist
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)

    # Define icon path (platform-specific format)
    if is_mac:
        icon_path = 'app_icon.icns' if os.path.exists('app_icon.icns') else None
    else:
        icon_path = 'app_icon.ico' if os.path.exists('app_icon.ico') else None

    if icon_path is None:
        print("Warning: No icon file found. The executable will use a default icon.")
    else:
        print(f"Using icon: {icon_path}")

    # Check if ffmpeg exists in the project directory
    ffmpeg_name = 'ffmpeg' if is_mac else 'ffmpeg.exe'
    ffmpeg_exists = os.path.exists(ffmpeg_name)
    if not ffmpeg_exists:
        print(f"Warning: {ffmpeg_name} not found in the project directory.")
        print("The application will still build, but users will need to install FFmpeg separately.")
        if is_mac:
            print("Install via Homebrew: brew install ffmpeg")
        else:
            print("For full functionality, download FFmpeg and place it in the same directory as the executable.")

    # Build the PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=Nabbr',
        '--onefile',
        '--windowed',
        '--clean',
    ]

    # Add icon if available
    if icon_path:
        cmd.append(f'--icon={icon_path}')

    # Add ffmpeg if available
    if ffmpeg_exists:
        cmd.append(f'--add-data={ffmpeg_name}{path_sep}.')

    # Add hidden imports
    cmd.extend([
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=yt_dlp',
        '--hidden-import=curl_cffi',
    ])

    # Add the main script
    cmd.append('video_downloader_ui.py')

    # Run PyInstaller
    print("\nRunning PyInstaller with the following command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    print("\nBuild completed!")
    print(f"Created: {os.path.abspath('dist/' + app_name)}")

    # Copy additional files to the dist directory
    print("\nCopying additional files to distribution directory...")

    # Create a simple readme for users
    with open('dist/README.txt', 'w') as f:
        f.write(f"""Nabbr
=====

Download videos and audio from YouTube, Instagram, TikTok, and 1000+ sites.

Features:
- Download videos in various qualities
- Convert for Adobe Premiere Pro and DaVinci Resolve
- Extract audio as MP3
- Batch download multiple videos

To use:
1. Launch {app_name}
2. Enter a video URL
3. Select your desired options
4. Click Download

For batch downloads:
1. Check the "Batch Mode" checkbox
2. Add multiple URLs to the queue
3. Click "Download All"

Note: This application requires an internet connection.
""")

    # If ffmpeg wasn't included, create a note about it
    if not ffmpeg_exists:
        with open('dist/FFMPEG_NOTE.txt', 'w') as f:
            if is_mac:
                f.write("""IMPORTANT: FFmpeg Required for Full Functionality
===========================================

For video conversion features to work properly, you need to install FFmpeg:

1. Install via Homebrew: brew install ffmpeg
   Or download from: https://ffmpeg.org/download.html

Without FFmpeg, you can still download videos, but conversion for
Adobe Premiere Pro and DaVinci Resolve will not work.
""")
            else:
                f.write("""IMPORTANT: FFmpeg Required for Full Functionality
===========================================

For video conversion features to work properly, you need to install FFmpeg:

1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract the archive and locate ffmpeg.exe
3. Place ffmpeg.exe in the same directory as Nabbr.exe

Without FFmpeg, you can still download videos, but conversion for
Adobe Premiere Pro and DaVinci Resolve will not work.
""")

    print("\nDistribution package is ready!")
    print(f"You can find it at: {os.path.abspath('dist')}")

if __name__ == "__main__":
    build_executable()
