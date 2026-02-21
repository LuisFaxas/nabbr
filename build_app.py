#!/usr/bin/env python
"""
Build Script for Nabbr
Creates a standalone executable using PyInstaller
"""

import os
import shutil
import subprocess
import sys

def build_executable():
    """Build a standalone executable for Nabbr."""

    print("Building Nabbr executable...")

    # Clean previous build directories if they exist
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)

    # Define icon path
    icon_path = 'app_icon.ico'
    if not os.path.exists(icon_path):
        print("Warning: No icon file found. The executable will use a default icon.")
        icon_path = None
    else:
        print(f"Using icon: {icon_path}")

    # Check if ffmpeg.exe exists in the project directory
    ffmpeg_exists = os.path.exists('ffmpeg.exe')
    if not ffmpeg_exists:
        print("Warning: ffmpeg.exe not found in the project directory.")
        print("The application will still build, but users will need to install FFmpeg separately.")
        print("For full functionality, download FFmpeg and place it in the same directory as the executable.")

    # Build the PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=Nabbr',
        '--onefile',  # Create a single executable file
        '--windowed',  # Don't show console window when running the app
        '--clean',  # Clean PyInstaller cache
    ]

    # Add icon if available
    if icon_path:
        cmd.append(f'--icon={icon_path}')

    # Add ffmpeg if available
    if ffmpeg_exists:
        cmd.append('--add-data=ffmpeg.exe;.')

    # Add hidden imports that might be needed
    cmd.extend([
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=yt_dlp',
    ])

    # Add the main script
    cmd.append('video_downloader_ui.py')

    # Run PyInstaller
    print("\nRunning PyInstaller with the following command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    print("\nBuild completed!")
    print(f"Executable created at: {os.path.abspath('dist/Nabbr.exe')}")

    # Copy additional files to the dist directory
    print("\nCopying additional files to distribution directory...")

    # Create a simple readme for users
    with open('dist/README.txt', 'w') as f:
        f.write("""Nabbr
=====

Download videos and audio from YouTube, Instagram, TikTok, and 1000+ sites.

Features:
- Download videos in various qualities
- Convert for Adobe Premiere Pro and DaVinci Resolve
- Extract audio as MP3
- Batch download multiple videos

To use:
1. Launch Nabbr.exe
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
