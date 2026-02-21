#!/usr/bin/env python
"""
Update yt-dlp and test YouTube downloads
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def main():
    print("🚀 YouTube Downloader Fix Script")
    print("=" * 50)
    
    # Step 1: Update yt-dlp
    if not run_command("pip install --upgrade yt-dlp", "Updating yt-dlp"):
        print("⚠️ Failed to update yt-dlp, continuing with current version...")
    
    # Step 2: Check yt-dlp version
    run_command("yt-dlp --version", "Checking yt-dlp version")
    
    # Step 3: Clear yt-dlp cache
    run_command("yt-dlp --rm-cache-dir", "Clearing yt-dlp cache")
    
    # Step 4: Test with a simple YouTube video
    print("\n🧪 Testing YouTube download...")
    test_url = "https://www.youtube.com/watch?v=LasrD6SZkZk"
    
    # Try basic info extraction first
    test_cmd = f'yt-dlp --no-playlist --simulate --print "%(title)s" "{test_url}"'
    if run_command(test_cmd, "Testing video info extraction"):
        print("🎉 YouTube extraction is working!")
        
        # Test actual download
        output_dir = "."
        download_cmd = f'yt-dlp --no-playlist -f "best[height<=720]" --extract-flat --simulate "{test_url}"'
        run_command(download_cmd, "Testing download simulation")
    else:
        print("❌ YouTube extraction failed")
        print("\n💡 Suggestions:")
        print("1. Check your internet connection")
        print("2. Try a different YouTube URL")
        print("3. YouTube may have changed their API - check yt-dlp issues on GitHub")
        print("4. Consider using a VPN if you're in a restricted region")
    
    print("\n" + "=" * 50)
    print("🏁 Fix script completed")

if __name__ == "__main__":
    main()
