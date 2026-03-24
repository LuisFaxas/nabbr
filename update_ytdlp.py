#!/usr/bin/env python
"""
Update yt-dlp and test YouTube downloads
"""

import subprocess
import sys
import os

# On Windows, prevent subprocess calls from spawning visible console windows
_subprocess_flags = {}
if sys.platform == 'win32':
    _subprocess_flags['creationflags'] = subprocess.CREATE_NO_WINDOW

def run_command(command, description):
    """Run a command (list of args) and return success status"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True,
                                **_subprocess_flags)
        print(f"{description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} failed")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def main():
    print("Nabbr - yt-dlp Update Script")
    print("=" * 50)

    # Step 1: Update yt-dlp
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                       "Updating yt-dlp"):
        print("Failed to update yt-dlp, continuing with current version...")

    # Step 2: Check yt-dlp version
    run_command(["yt-dlp", "--version"], "Checking yt-dlp version")

    # Step 3: Clear yt-dlp cache
    run_command(["yt-dlp", "--rm-cache-dir"], "Clearing yt-dlp cache")

    # Step 4: Test with a simple YouTube video
    print("\nTesting YouTube download...")
    test_url = "https://www.youtube.com/watch?v=LasrD6SZkZk"

    # Try basic info extraction first
    if run_command(["yt-dlp", "--no-playlist", "--simulate", "--print", "%(title)s", test_url],
                   "Testing video info extraction"):
        print("YouTube extraction is working!")

        # Test actual download
        run_command(["yt-dlp", "--no-playlist", "-f", "best[height<=720]",
                     "--extract-flat", "--simulate", test_url],
                    "Testing download simulation")
    else:
        print("YouTube extraction failed")
        print("\nSuggestions:")
        print("1. Check your internet connection")
        print("2. Try a different YouTube URL")
        print("3. YouTube may have changed their API - check yt-dlp issues on GitHub")
        print("4. Consider using a VPN if you're in a restricted region")

    print("\n" + "=" * 50)
    print("Update script completed")

if __name__ == "__main__":
    main()
