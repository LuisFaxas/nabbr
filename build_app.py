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
    is_win = sys.platform == 'win32'
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
    if ffmpeg_exists:
        print(f"Found {ffmpeg_name} — will bundle it into the executable.")
    else:
        print(f"Warning: {ffmpeg_name} not found in the project directory.")
        print("The app will still work for basic downloads, but editor conversions need FFmpeg.")
        if is_win:
            print("To bundle FFmpeg: download ffmpeg.exe and place it in this directory before building.")
            print("Or users can place ffmpeg.exe next to Nabbr.exe after building.")
        else:
            print("Install via Homebrew: brew install ffmpeg")

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

    # Bundle icon files so the running app can load them at runtime
    for icon_file in ['app_icon.ico', 'app_icon.png']:
        if os.path.exists(icon_file):
            cmd.append(f'--add-data={icon_file}{path_sep}.')
            print(f"Bundling {icon_file} for runtime icon display.")

    # Add ffmpeg if available
    if ffmpeg_exists:
        cmd.append(f'--add-data={ffmpeg_name}{path_sep}.')

    # Add deno (JS runtime required by yt-dlp for YouTube) if available
    deno_name = 'deno' if is_mac else 'deno.exe'
    deno_exists = os.path.exists(deno_name)
    if deno_exists:
        print(f"Found {deno_name} — will bundle it (JS runtime for yt-dlp YouTube support).")
        cmd.append(f'--add-data={deno_name}{path_sep}.')
    else:
        print(f"Warning: {deno_name} not found. YouTube downloads may fail without a JS runtime.")

    # Hidden imports — PyQt5, yt-dlp, and curl_cffi (native C extensions need explicit listing)
    cmd.extend([
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=yt_dlp',
        '--hidden-import=curl_cffi',
        '--hidden-import=curl_cffi.requests',
        '--hidden-import=curl_cffi._wrapper',
        '--hidden-import=certifi',
    ])

    # Collect all curl_cffi data files (native .dll/.so libraries)
    cmd.extend([
        '--collect-all=curl_cffi',
    ])

    # Add the main script
    cmd.append('video_downloader_ui.py')

    # Run PyInstaller
    print("\nRunning PyInstaller with the following command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    print("\nBuild completed!")
    print(f"Created: {os.path.abspath(os.path.join('dist', app_name))}")

    # If ffmpeg wasn't included, create a note about it
    if not ffmpeg_exists:
        note_path = os.path.join('dist', 'FFMPEG_NOTE.txt')
        with open(note_path, 'w') as f:
            if is_mac:
                f.write("""FFmpeg Required for Editor Conversions
======================================

For Premiere Pro / DaVinci Resolve conversion features, install FFmpeg:

  brew install ffmpeg

Basic video/audio downloads work without FFmpeg.
""")
            else:
                f.write("""FFmpeg Required for Editor Conversions
======================================

For Premiere Pro / DaVinci Resolve conversion features:

  1. Download ffmpeg.exe from https://ffmpeg.org/download.html
     (or https://github.com/BtbN/FFmpeg-Builds/releases — get the
     "ffmpeg-master-latest-win64-gpl.zip", extract, find ffmpeg.exe in the bin/ folder)
  2. Place ffmpeg.exe in the SAME FOLDER as Nabbr.exe

Basic video/audio downloads work without FFmpeg.
""")

    print("\nDistribution package is ready!")
    print(f"You can find it at: {os.path.abspath('dist')}")

    if ffmpeg_exists:
        print(f"\n  Portable package: just copy dist/{app_name} anywhere and double-click to run!")
    else:
        print(f"\n  To make fully portable: place ffmpeg.exe next to dist/{app_name}")

if __name__ == "__main__":
    build_executable()
