#!/usr/bin/env python
"""
Settings Manager for Web Video Downloader
Handles saving and loading user preferences including last used directories.
"""

import os
import json
import time
import copy
from pathlib import Path

class SettingsManager:
    def __init__(self):
        # Create settings directory in user's home directory
        self.settings_dir = Path.home() / ".nabbr"
        self.settings_file = self.settings_dir / "settings.json"
        
        # Create settings directory if it doesn't exist
        self.settings_dir.mkdir(exist_ok=True)
        
        # Default settings
        self.default_settings = {
            "last_download_directory": str(Path.home() / "Downloads"),
            "default_quality": "best",
            "default_audio_quality": "192",
            "remember_window_size": True,
            "window_width": 900,
            "window_height": 650,
            "auto_convert": True,
            "default_editor": "premiere",  # premiere or davinci
            "enable_subtitles": False,
            "preferred_format": "mp4",
            "recent_directories": [],
            "max_recent_directories": 5,
            "auto_update_yt_dlp": True,
            "download_history": [],
            "max_download_history": 20,
        }
        
        # Load existing settings
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file, or create default settings"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                settings = copy.deepcopy(self.default_settings)
                settings.update(loaded_settings)
                
                # Validate that directories exist
                if not os.path.exists(settings["last_download_directory"]):
                    settings["last_download_directory"] = str(Path.home() / "Downloads")
                
                return settings
            else:
                # Create default settings file
                self.save_settings(self.default_settings)
                return copy.deepcopy(self.default_settings)
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            return copy.deepcopy(self.default_settings)

    def save_settings(self, settings=None):
        """Save settings to file"""
        try:
            if settings is None:
                settings = self.settings
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value and save"""
        self.settings[key] = value
        self.save_settings()
    
    def get_settings_file_path(self):
        """Get the path to the settings file"""
        return str(self.settings_file)

    def get_last_download_directory(self):
        """Get the last used download directory"""
        return self.settings.get("last_download_directory", str(Path.home() / "Downloads"))
    
    def set_last_download_directory(self, directory):
        """Set the last used download directory"""
        if os.path.exists(directory):
            self.settings["last_download_directory"] = directory
            self.add_recent_directory(directory)
    
    def add_recent_directory(self, directory):
        """Add a directory to the recent directories list"""
        recent = self.settings.get("recent_directories", [])
        
        # Remove if already exists
        if directory in recent:
            recent.remove(directory)
        
        # Add to beginning
        recent.insert(0, directory)
        
        # Keep only max_recent_directories items
        max_recent = self.settings.get("max_recent_directories", 5)
        recent = recent[:max_recent]
        
        # Filter out non-existent directories
        recent = [d for d in recent if os.path.exists(d)]
        
        self.settings["recent_directories"] = recent
        self.save_settings()
    
    def get_recent_directories(self):
        """Get list of recent directories"""
        recent = self.settings.get("recent_directories", [])
        # Filter out non-existent directories
        recent = [d for d in recent if os.path.exists(d)]
        return recent
    
    def add_download_history(self, url, title, output_path):
        """Add a download to the history"""
        history = self.settings.get("download_history", [])
        
        # Create history entry
        entry = {
            "url": url,
            "title": title,
            "output_path": output_path,
            "timestamp": str(time.time())
        }
        
        # Remove duplicate URLs
        history = [h for h in history if h.get("url") != url]
        
        # Add to beginning
        history.insert(0, entry)
        
        # Keep only max_download_history items
        max_history = self.settings.get("max_download_history", 20)
        history = history[:max_history]
        
        self.settings["download_history"] = history
        self.save_settings()
    
    def get_download_history(self):
        """Get download history"""
        return self.settings.get("download_history", [])
    
    def clear_download_history(self):
        """Clear download history"""
        self.settings["download_history"] = []
        self.save_settings()
    
    def get_window_settings(self):
        """Get window size and position settings"""
        return {
            "width": self.settings.get("window_width", 950),
            "height": self.settings.get("window_height", 750),
            "remember": self.settings.get("remember_window_size", True)
        }
    
    def set_window_settings(self, width, height):
        """Set window size settings"""
        if self.settings.get("remember_window_size", True):
            self.settings["window_width"] = width
            self.settings["window_height"] = height
            self.save_settings()
    
    def get_default_options(self):
        """Get default download options"""
        return {
            "quality": self.settings.get("default_quality", "best"),
            "audio_quality": self.settings.get("default_audio_quality", "192"),
            "auto_convert": self.settings.get("auto_convert", True),
            "default_editor": self.settings.get("default_editor", "premiere"),
            "enable_subtitles": self.settings.get("enable_subtitles", False),
            "preferred_format": self.settings.get("preferred_format", "mp4"),
        }
    
    def export_settings(self, file_path):
        """Export settings to a file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, file_path):
        """Import settings from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Merge with current settings
            self.settings.update(imported_settings)
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            self.settings = copy.deepcopy(self.default_settings)
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error resetting settings: {e}")
            return False
