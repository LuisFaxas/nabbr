#!/usr/bin/env python
"""
Nabbr
A desktop video and audio downloader.
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QCheckBox, QProgressBar, QFileDialog,
                             QTabWidget, QGroupBox, QMessageBox, QListWidget,
                             QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import video_downloader
import glob
from pathlib import Path
from settings_manager import SettingsManager

class ProgressMonitor:
    def __init__(self, progress_callback, status_callback, thread=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.current_phase = "download"
        self._thread = thread

    def update_progress(self, progress_dict):
        # This function will be called by yt-dlp to report progress
        try:
            # Check if cancellation was requested
            if self._thread and self._thread._stop_requested:
                raise DownloadCancelled("Download cancelled by user")
            if self.current_phase == "download":
                if progress_dict.get('status') == 'downloading':
                    # Calculate download progress
                    if 'total_bytes' in progress_dict and progress_dict['total_bytes'] > 0:
                        percent = int(progress_dict['downloaded_bytes'] / progress_dict['total_bytes'] * 100)
                        self.progress_callback.emit(percent)
                        
                        # Update status with download speed and ETA
                        if 'speed' in progress_dict and progress_dict['speed'] is not None:
                            speed = progress_dict['speed'] / 1024 / 1024  # Convert to MB/s
                            eta = progress_dict.get('eta', 0)
                            status = f"Downloading: {percent}% at {speed:.2f} MB/s, ETA: {eta} seconds"
                            self.status_callback.emit(status)
                    # Handle case where total_bytes is not available
                    elif 'downloaded_bytes' in progress_dict:
                        self.status_callback.emit(f"Downloading: {progress_dict['downloaded_bytes'] / 1024 / 1024:.1f} MB downloaded")
                        # Use indeterminate progress
                        self.progress_callback.emit(-1)
                        
                elif progress_dict.get('status') == 'finished':
                    self.status_callback.emit("Download finished, processing file...")
                    self.current_phase = "processing"
                    self.progress_callback.emit(50)  # Set to 50% for processing phase
            
            elif self.current_phase == "processing" and progress_dict.get('status') == 'finished':
                self.progress_callback.emit(90)  # Almost done
                self.status_callback.emit("Processing complete, finalizing...")
        except Exception as e:
            # Don't let errors in progress reporting crash the download
            self.status_callback.emit(f"Progress update error: {str(e)}")
            print(f"Progress update error: {str(e)}")


class DownloadCancelled(Exception):
    """Raised when a download is cancelled by the user."""
    pass


class DownloaderThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, url, output_path, options):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.options = options
        self._stop_requested = False
        self.monitor = ProgressMonitor(self.progress, self.status, self)

    def request_stop(self):
        """Request graceful stop. The progress hook will raise DownloadCancelled."""
        self._stop_requested = True
    
    def run(self):
        try:
            # Initialize progress and status
            self.progress.emit(0)
            self.status.emit("🚀 Starting download...")

            # Reset progress monitor phase for each download
            self.monitor.current_phase = "download"

            # Use the improved backend download function
            exit_code = video_downloader.download_video(
                url=self.url,
                output_path=self.output_path,
                video_format=self.options.get('format'),
                audio_only=self.options.get('audio_only', False),
                subtitle=self.options.get('subtitle', False),
                quality=self.options.get('quality'),
                mp4=self.options.get('mp4', False),
                premiere=self.options.get('premiere', False),
                davinci=self.options.get('davinci', False),
                direct_convert=self.options.get('convert', False),
                audio_quality=self.options.get('audio_quality', '192'),
                progress_hook=self.monitor.update_progress,
            )
            
            if exit_code == 0:
                # Check if files were actually downloaded
                if self.output_path:
                    # Look for any video/audio files that might have been downloaded
                    if self.options.get('audio_only'):
                        # For audio downloads, prioritize audio formats
                        file_extensions = ['*.mp3', '*.m4a', '*.aac', '*.opus']
                    else:
                        # For video downloads, prioritize video formats
                        file_extensions = ['*.mp4', '*.mkv', '*.webm', '*.mov', '*.avi']
                    
                    found_files = []
                    
                    for ext in file_extensions:
                        files = glob.glob(f"{self.output_path}/{ext}")
                        found_files.extend(files)
                    
                    if found_files:
                        # Sort by creation time to find the most recent file
                        latest_file = max(found_files, key=os.path.getctime)
                        file_name = os.path.basename(latest_file)
                        
                        # Update status based on file type
                        if self.options.get('audio_only'):
                            if file_name.lower().endswith('.mp3'):
                                self.status.emit(f"🎵 Success! MP3 audio extracted: {file_name}")
                            elif file_name.lower().endswith(('.m4a', '.aac', '.opus')):
                                self.status.emit(f"🎵 Audio downloaded: {file_name}")
                            else:
                                self.status.emit(f"📁 File downloaded: {file_name}")
                        else:
                            if self.options.get('davinci') and '_davinci' in file_name:
                                self.status.emit(f"🎬 DaVinci-ready video: {file_name}")
                            elif self.options.get('premiere') and '_premiere' in file_name:
                                self.status.emit(f"🎬 Premiere-ready video: {file_name}")
                            else:
                                self.status.emit(f"📹 Video downloaded: {file_name}")
                        
                        # Make sure progress is at 100% when done
                        self.progress.emit(100)
                        self.finished_signal.emit(True, f"Download completed successfully: {file_name}")
                    else:
                        # No files found, might be an error
                        self.progress.emit(0)
                        self.finished_signal.emit(False, "No files were downloaded. Check the URL and try again.")
                else:
                    # No output path specified, assume success
                    self.progress.emit(100)
                    self.finished_signal.emit(True, "Download completed successfully!")
            else:
                # Download failed
                self.progress.emit(0)
                self.finished_signal.emit(False, "Download failed. Please check the URL and try again.")
                
        except DownloadCancelled:
            self.progress.emit(0)
            self.finished_signal.emit(False, "Download cancelled.")
        except Exception as e:
            self.progress.emit(0)  # Reset progress on error
            self.finished_signal.emit(False, f"Error: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings manager
        self.settings = SettingsManager()
        
        self.setWindowTitle("📹 Nabbr - Ready")
        
        # Debounce timer for saving window size on resize
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(500)
        self._resize_timer.timeout.connect(self._save_window_size)

        # Track if we're in batch mode
        self.is_batch_mode = False
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # URL input section
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube, TikTok, Instagram, or other video URL")
        # Set maximum length to handle very long URLs
        self.url_input.setMaxLength(2048)  # Allow up to 2048 characters
        # Connect Enter key to add URL or start download
        self.url_input.returnPressed.connect(self.handle_url_input_enter)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Batch download section
        batch_layout = QHBoxLayout()
        self.batch_check = QCheckBox("Batch Download")
        self.batch_check.stateChanged.connect(self.toggle_batch_mode)
        batch_layout.addWidget(self.batch_check)
        self.add_url_btn = QPushButton("Add to Queue")
        self.add_url_btn.clicked.connect(self.add_url_to_queue)
        self.add_url_btn.setEnabled(False)
        batch_layout.addWidget(self.add_url_btn)
        main_layout.addLayout(batch_layout)
        
        # URL queue display
        self.url_queue_label = QLabel("Download Queue (0 items)")
        self.url_queue_label.setVisible(False)
        main_layout.addWidget(self.url_queue_label)
        
        self.url_queue = QListWidget()
        self.url_queue.setVisible(False)
        self.url_queue.setMinimumHeight(150)  # Increased minimum height
        self.url_queue.setMaximumHeight(200)  # Increased maximum height
        main_layout.addWidget(self.url_queue)
        
        # Queue control buttons
        queue_controls = QHBoxLayout()
        self.remove_url_btn = QPushButton("Remove Selected")
        self.remove_url_btn.clicked.connect(self.remove_url_from_queue)
        self.remove_url_btn.setEnabled(False)
        queue_controls.addWidget(self.remove_url_btn)
        
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        self.clear_queue_btn.setEnabled(False)
        queue_controls.addWidget(self.clear_queue_btn)
        
        queue_control_widget = QWidget()
        queue_control_widget.setLayout(queue_controls)
        queue_control_widget.setVisible(False)
        self.queue_control_widget = queue_control_widget
        main_layout.addWidget(queue_control_widget)
        
        # Tabs for different settings
        tabs = QTabWidget()
        
        # Basic settings tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        
        # Output directory with recent directories
        output_group = QGroupBox("📁 Output Directory")
        output_group_layout = QVBoxLayout()
        
        # Main output directory selection
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Save to:"))
        self.output_path = QLineEdit()
        # Load saved directory
        self.output_path.setText(self.settings.get_last_download_directory())
        output_layout.addWidget(self.output_path)
        
        browse_btn = QPushButton("📂 Browse...")
        browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_btn)
        
        # Recent directories dropdown
        recent_btn = QPushButton("🕰️ Recent")
        recent_btn.setMaximumWidth(80)
        recent_btn.clicked.connect(self.show_recent_directories)
        output_layout.addWidget(recent_btn)
        
        output_group_layout.addLayout(output_layout)
        
        # Quick access buttons for common directories
        quick_layout = QHBoxLayout()
        downloads_btn = QPushButton("📥 Downloads")
        downloads_btn.clicked.connect(lambda: self.set_quick_directory(str(Path.home() / "Downloads")))
        quick_layout.addWidget(downloads_btn)
        
        desktop_btn = QPushButton("🗺️ Desktop")
        desktop_btn.clicked.connect(lambda: self.set_quick_directory(str(Path.home() / "Desktop")))
        quick_layout.addWidget(desktop_btn)
        
        videos_btn = QPushButton("📹 Videos")
        videos_btn.clicked.connect(lambda: self.set_quick_directory(str(Path.home() / "Videos")))
        quick_layout.addWidget(videos_btn)
        
        quick_layout.addStretch()
        output_group_layout.addLayout(quick_layout)
        
        output_group.setLayout(output_group_layout)
        basic_layout.addWidget(output_group)
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "worst"])
        quality_layout.addWidget(self.quality_combo)
        basic_layout.addLayout(quality_layout)
        
        # Download Type Selection
        download_type_group = QGroupBox(" What do you want to download?")
        download_type_layout = QVBoxLayout()
        
        # Add helpful description
        type_description = QLabel(
            " Choose your download type - everything else will be configured automatically!"
        )
        type_description.setStyleSheet(
            "color: #2E7D32; font-weight: bold; font-style: italic; margin-bottom: 10px; "
            "padding: 8px; background-color: #E8F5E8; border-radius: 5px;"
        )
        download_type_layout.addWidget(type_description)
        
        # Radio buttons for download type
        self.video_radio = QCheckBox(" Video (MP4)")
        self.video_radio.setChecked(True)
        self.video_radio.setStyleSheet("font-size: 12px; font-weight: bold;")
        download_type_layout.addWidget(self.video_radio)
        
        self.audio_radio = QCheckBox("🎵 Audio Only (MP3)")
        self.audio_radio.setStyleSheet("font-size: 12px; font-weight: bold; color: #2E7D32;")
        download_type_layout.addWidget(self.audio_radio)
        
        # Connect checkboxes to ensure only one is selected
        self.video_radio.stateChanged.connect(self.on_video_type_changed)
        self.audio_radio.stateChanged.connect(self.on_audio_type_changed)
        
        # Audio quality selection (hidden by default)
        self.audio_quality_layout = QHBoxLayout()
        audio_quality_label = QLabel("  Audio Quality:")
        audio_quality_label.setStyleSheet("color: #666; margin-left: 20px;")
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["192 kbps (High)", "128 kbps (Medium)", "96 kbps (Low)"])
        self.audio_quality_layout.addWidget(audio_quality_label)
        self.audio_quality_layout.addWidget(self.audio_quality_combo)
        
        # Create widget to hold audio quality options
        self.audio_quality_widget = QWidget()
        self.audio_quality_widget.setLayout(self.audio_quality_layout)
        self.audio_quality_widget.setVisible(False)
        download_type_layout.addWidget(self.audio_quality_widget)
        
        download_type_group.setLayout(download_type_layout)
        basic_layout.addWidget(download_type_group)
        
        # Video Format Options (visible by default)
        self.video_options_group = QGroupBox("📹 Video Options")
        video_options_layout = QVBoxLayout()
        
        self.subtitle_check = QCheckBox("📝 Download Subtitles")
        video_options_layout.addWidget(self.subtitle_check)
        
        # Add video quality note
        video_note = QLabel(
            "✅ Automatically configured for video editing compatibility!\n"
            "Video will be downloaded in MP4 format with Premiere Pro settings."
        )
        video_note.setStyleSheet(
            "color: #666; font-size: 10px; padding: 5px; "
            "background-color: #F5F5F5; border-radius: 3px;"
        )
        video_note.setWordWrap(True)
        video_options_layout.addWidget(video_note)
        
        self.video_options_group.setLayout(video_options_layout)
        basic_layout.addWidget(self.video_options_group)
        
        # Audio Instructions and Options (only visible for audio downloads)
        self.audio_instructions_group = QGroupBox("🎵 Audio Download Guide")
        audio_instructions_layout = QVBoxLayout()
        
        # Step-by-step instructions
        instructions_text = QLabel(
            "✅ Perfect! You've selected Audio Only mode.\n\n"
            "🎵 Everything is now automatically configured for MP3 downloads!\n\n"
            "📋 Just follow these simple steps:\n"
            "1. Choose your audio quality above\n"
            "2. Paste any video URL (YouTube, Instagram, TikTok, etc.)\n"
            "3. Click Download to get your MP3 file\n\n"
            "🤖 Note: All video options are automatically disabled - you don't need to worry about them!"
        )
        instructions_text.setStyleSheet(
            "color: #2E7D32; font-size: 11px; padding: 12px; "
            "background-color: #E8F5E8; border-radius: 5px; border: 1px solid #4CAF50;"
        )
        instructions_text.setWordWrap(True)
        audio_instructions_layout.addWidget(instructions_text)
        
        # Audio-specific options
        audio_options_title = QLabel("🎚️ Audio Settings:")
        audio_options_title.setStyleSheet("font-weight: bold; color: #2E7D32; margin-top: 10px;")
        audio_instructions_layout.addWidget(audio_options_title)
        
        # File naming option
        self.audio_filename_check = QCheckBox("📁 Use original video title as filename")
        self.audio_filename_check.setChecked(True)
        audio_instructions_layout.addWidget(self.audio_filename_check)
        
        # Metadata preservation
        self.audio_metadata_check = QCheckBox("📱 Preserve audio metadata (title, artist, etc.)")
        self.audio_metadata_check.setChecked(True)
        audio_instructions_layout.addWidget(self.audio_metadata_check)
        
        self.audio_instructions_group.setLayout(audio_instructions_layout)
        self.audio_instructions_group.setVisible(False)  # Hidden by default
        basic_layout.addWidget(self.audio_instructions_group)
        
        # Video Editor Compatibility (only visible for video downloads)
        self.editor_group = QGroupBox("🎬 Video Editor Compatibility")
        editor_layout = QVBoxLayout()
        
        # Premiere Pro option
        self.premiere_check = QCheckBox("✨ Adobe Premiere Pro Compatible")
        self.premiere_check.setChecked(True)
        self.premiere_check.setStyleSheet("font-weight: bold; color: #7B1FA2;")
        editor_layout.addWidget(self.premiere_check)
        
        # DaVinci Resolve option
        self.davinci_check = QCheckBox("🎨 DaVinci Resolve Compatible")
        self.davinci_check.setChecked(False)
        self.davinci_check.setStyleSheet("font-weight: bold; color: #FF6B35;")
        editor_layout.addWidget(self.davinci_check)
        
        # Connect checkboxes to convert checkbox and ensure mutual exclusivity
        self.premiere_check.stateChanged.connect(self.update_convert_state)
        self.davinci_check.stateChanged.connect(self.update_convert_state)
        self.premiere_check.stateChanged.connect(lambda state: self.handle_editor_selection('premiere', state))
        self.davinci_check.stateChanged.connect(lambda state: self.handle_editor_selection('davinci', state))
        
        self.convert_check = QCheckBox("🔧 Convert with FFmpeg (recommended)")
        self.convert_check.setChecked(True)
        editor_layout.addWidget(self.convert_check)
        
        # Add explanation for video conversion
        video_convert_note = QLabel(
            "✅ These options are automatically enabled for the best video editing experience.\n"
            "Your video will work perfectly in Adobe Premiere Pro, DaVinci Resolve, and other editors!"
        )
        video_convert_note.setStyleSheet(
            "color: #666; font-size: 10px; padding: 5px; "
            "background-color: #F5F5F5; border-radius: 3px;"
        )
        video_convert_note.setWordWrap(True)
        editor_layout.addWidget(video_convert_note)
        
        self.editor_group.setLayout(editor_layout)
        basic_layout.addWidget(self.editor_group)
        
        basic_tab.setLayout(basic_layout)
        tabs.addTab(basic_tab, "Basic Settings")
        
        # Advanced settings tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout()
        
        # Platform selection
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Auto-detect", "YouTube", "TikTok", "Instagram", "Twitter", "Facebook", "Vimeo"])
        platform_layout.addWidget(self.platform_combo)
        advanced_layout.addLayout(platform_layout)
        
        # Instagram options (shown only when Instagram is selected)
        self.instagram_options = QGroupBox("Instagram Options")
        instagram_layout = QVBoxLayout()
        self.instagram_no_login = QCheckBox("Skip Login (Public Videos Only)")
        self.instagram_no_login.setChecked(True)
        instagram_layout.addWidget(self.instagram_no_login)
        self.instagram_options.setLayout(instagram_layout)
        self.instagram_options.setVisible(False)
        advanced_layout.addWidget(self.instagram_options)
        
        # Connect platform selection to show/hide platform-specific options
        self.platform_combo.currentTextChanged.connect(self.update_platform_options)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_input = QLineEdit()
        self.format_input.setPlaceholderText("e.g., bestvideo+bestaudio")
        format_layout.addWidget(self.format_input)
        advanced_layout.addLayout(format_layout)
        
        # Add a note about yt-dlp format strings
        note_label = QLabel("Note: Format uses yt-dlp format strings. Leave empty to use default.")
        note_label.setWordWrap(True)
        advanced_layout.addWidget(note_label)
        
        advanced_tab.setLayout(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")
        
        main_layout.addWidget(tabs)
        
        # Progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(25)  # Make progress bar taller
        progress_layout.addWidget(self.progress_bar)
        
        # Status label with fixed height
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumHeight(30)  # Fixed height for status label
        self.status_label.setWordWrap(True)  # Allow text wrapping
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Status label is now part of the progress group
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        main_layout.addWidget(self.download_btn)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create menu bar
        self.create_menu_bar()

        # Apply saved settings
        self.apply_default_settings()

        # Let Qt compute the size needed to show all content, then lock it as minimum
        self.adjustSize()
        self.setMinimumSize(self.size())

        # Apply saved window size (only grow beyond the computed minimum)
        window_settings = self.settings.get_window_settings()
        if window_settings["remember"]:
            min_w, min_h = self.minimumWidth(), self.minimumHeight()
            self.resize(max(window_settings["width"], min_w), max(window_settings["height"], min_h))
    
    def create_menu_bar(self):
        """Create menu bar with settings and options"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('📁 File')
        
        # Export settings
        export_action = QAction('💾 Export Settings...', self)
        export_action.triggered.connect(self.export_settings)
        file_menu.addAction(export_action)
        
        # Import settings
        import_action = QAction('📂 Import Settings...', self)
        import_action.triggered.connect(self.import_settings)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('🚪 Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('⚙️ Settings')
        
        # Set default directory
        default_dir_action = QAction('📁 Set Default Directory...', self)
        default_dir_action.triggered.connect(self.set_default_directory)
        settings_menu.addAction(default_dir_action)
        
        # Clear recent directories
        clear_recent_action = QAction('🕰️ Clear Recent Directories', self)
        clear_recent_action.triggered.connect(self.clear_recent_directories)
        settings_menu.addAction(clear_recent_action)
        
        settings_menu.addSeparator()
        
        # Download history
        history_action = QAction('📈 View Download History', self)
        history_action.triggered.connect(self.show_download_history)
        settings_menu.addAction(history_action)
        
        # Clear download history
        clear_history_action = QAction('🖺 Clear Download History', self)
        clear_history_action.triggered.connect(self.clear_download_history)
        settings_menu.addAction(clear_history_action)
        
        settings_menu.addSeparator()
        
        # Reset to defaults
        reset_action = QAction('🔄 Reset to Defaults', self)
        reset_action.triggered.connect(self.reset_settings)
        settings_menu.addAction(reset_action)
        
        # Help menu
        help_menu = menubar.addMenu('❓ Help')
        
        # About
        about_action = QAction('ℹ️ About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Settings location
        settings_location_action = QAction('📄 Settings File Location', self)
        settings_location_action.triggered.connect(self.show_settings_location)
        help_menu.addAction(settings_location_action)
    
    def export_settings(self):
        """Export settings to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "nabbr_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            if self.settings.export_settings(file_path):
                QMessageBox.information(self, "Export Successful", f"Settings exported to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export settings.")
    
    def import_settings(self):
        """Import settings from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            if self.settings.import_settings(file_path):
                QMessageBox.information(self, "Import Successful", 
                                       "Settings imported successfully!\nRestart the application to see all changes.")
                # Apply some immediate changes
                self.apply_default_settings()
                self.output_path.setText(self.settings.get_last_download_directory())
            else:
                QMessageBox.warning(self, "Import Failed", "Failed to import settings.")
    
    def set_default_directory(self):
        """Set the default download directory"""
        current_dir = self.settings.get_last_download_directory()
        directory = QFileDialog.getExistingDirectory(self, "Set Default Directory", current_dir)
        if directory:
            self.settings.set_last_download_directory(directory)
            self.output_path.setText(directory)
            QMessageBox.information(self, "Default Directory Set", f"Default directory set to:\n{directory}")
    
    def clear_recent_directories(self):
        """Clear the recent directories list"""
        reply = QMessageBox.question(self, "Clear Recent Directories", 
                                   "Are you sure you want to clear all recent directories?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.set("recent_directories", [])
            QMessageBox.information(self, "Cleared", "Recent directories cleared.")
    
    def show_download_history(self):
        """Show download history dialog"""
        history = self.settings.get_download_history()
        if not history:
            QMessageBox.information(self, "Download History", "No download history found.")
            return
        
        # Create a simple dialog to show history
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Download History")
        dialog.setIcon(QMessageBox.Information)
        
        history_text = "Recent Downloads:\n\n"
        for i, entry in enumerate(history[:10], 1):  # Show last 10
            title = entry.get('title', 'Unknown')
            url = entry.get('url', 'Unknown')
            if len(title) > 50:
                title = title[:47] + "..."
            if len(url) > 60:
                url = url[:57] + "..."
            history_text += f"{i}. {title}\n   {url}\n\n"
        
        dialog.setText(history_text)
        dialog.exec_()
    
    def clear_download_history(self):
        """Clear download history"""
        reply = QMessageBox.question(self, "Clear Download History", 
                                   "Are you sure you want to clear all download history?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.clear_download_history()
            QMessageBox.information(self, "Cleared", "Download history cleared.")
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?\n" +
                                   "This will clear recent directories, download history, and preferences.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            QMessageBox.information(self, "Reset Complete", "Settings reset to defaults.\nRestart the application to see all changes.")
            # Apply immediate changes
            self.apply_default_settings()
            self.output_path.setText(self.settings.get_last_download_directory())
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Nabbr v2.0

A powerful video & audio downloader with support for:
• YouTube, TikTok, Instagram, Twitter/X and more
• Video and audio downloads
• Adobe Premiere Pro & DaVinci Resolve compatibility
• Batch downloads
• Smart format selection
• Download history and settings management

Built with yt-dlp and PyQt5

Features:
• Remembers your last used directory
• Recent directories for quick access
• Customizable quality settings
• Automatic video conversion for editing software
• YouTube SABR streaming workarounds"""
        
        QMessageBox.about(self, "About Nabbr", about_text)
    
    def show_settings_location(self):
        """Show the location of the settings file"""
        settings_path = self.settings.get_settings_file_path()
        QMessageBox.information(self, "Settings Location", 
                              f"Settings are stored at:\n{settings_path}\n\n" +
                              "You can backup this file to save your preferences.")
    
    def on_video_type_changed(self, state):
        """Handle video type selection - Make everything automatic for video downloads"""
        if state == Qt.Checked:
            self.audio_radio.setChecked(False)
            
            # AUTOMATIC VIDEO SETUP
            # Show video-related UI elements
            self.audio_quality_widget.setVisible(False)
            self.video_options_group.setVisible(True)
            self.editor_group.setVisible(True)
            # Hide audio-related UI elements
            self.audio_instructions_group.setVisible(False)
            
            # AUTOMATICALLY configure video settings for best experience
            self.premiere_check.setChecked(True)  # Enable Premiere Pro compatibility
            self.convert_check.setChecked(True)   # Enable FFmpeg conversion
            
            # Update window title to show current mode
            self.setWindowTitle("📹 Nabbr - Ready")
    
    def on_audio_type_changed(self, state):
        """Handle audio type selection - Make everything automatic for audio downloads"""
        if state == Qt.Checked:
            self.video_radio.setChecked(False)
            
            # AUTOMATIC AUDIO SETUP
            # Show audio-related UI elements
            self.audio_quality_widget.setVisible(True)
            self.audio_instructions_group.setVisible(True)
            # Hide video-related UI elements
            self.video_options_group.setVisible(False)
            self.editor_group.setVisible(False)
            
            # AUTOMATICALLY disable video-related options (they don't apply to audio)
            self.premiere_check.setChecked(False)  # Disable - not needed for audio
            self.convert_check.setChecked(False)   # Disable - audio has its own conversion
            self.subtitle_check.setChecked(False)  # Disable - no subtitles for audio
            
            # Update window title to show current mode
            self.setWindowTitle("Nabbr - Audio Mode")
            
        else:
            # Hide audio-related UI elements
            self.audio_quality_widget.setVisible(False)
            self.audio_instructions_group.setVisible(False)
            # Show video-related UI elements if no video option is selected
            if not self.video_radio.isChecked():
                self.video_radio.setChecked(True)
                self.video_options_group.setVisible(True)
                self.editor_group.setVisible(True)
                # Restore video defaults
                self.premiere_check.setChecked(True)
                self.convert_check.setChecked(True)
                self.setWindowTitle("📹 Nabbr - Ready")
    
    def update_convert_state(self, state):
        # If premiere or davinci is checked, also check convert
        if state == Qt.Checked:
            self.convert_check.setChecked(True)
    
    def handle_editor_selection(self, editor_type, state):
        """Handle mutual exclusivity between Premiere and DaVinci options"""
        if state == Qt.Checked:
            if editor_type == 'premiere':
                # Uncheck DaVinci when Premiere is selected
                self.davinci_check.blockSignals(True)
                self.davinci_check.setChecked(False)
                self.davinci_check.blockSignals(False)
            elif editor_type == 'davinci':
                # Uncheck Premiere when DaVinci is selected
                self.premiere_check.blockSignals(True)
                self.premiere_check.setChecked(False)
                self.premiere_check.blockSignals(False)
    
    def update_platform_options(self, platform):
        """Show/hide platform-specific options based on selected platform"""
        # Show Instagram options only when Instagram is selected
        self.instagram_options.setVisible(platform == "Instagram")
    
    def handle_url_input_enter(self):
        """Handle Enter key in URL input"""
        if self.batch_check.isChecked():
            self.add_url_to_queue()
        else:
            self.start_download()
    
    def toggle_batch_mode(self, state):
        # Show or hide batch download UI elements based on checkbox state
        is_batch = state == Qt.Checked
        self.is_batch_mode = is_batch  # Update tracking variable
        
        self.add_url_btn.setEnabled(is_batch)
        self.url_queue_label.setVisible(is_batch)
        self.url_queue.setVisible(is_batch)
        self.queue_control_widget.setVisible(is_batch)
        
        # Change download button text based on mode
        if is_batch:
            self.download_btn.setText("Download All")
            # Grow window if needed to fit batch UI, never shrink
            if self.height() < 900:
                self.resize(self.width(), 900)
        else:
            self.download_btn.setText("Download")
    
    def add_url_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL")
            return
        
        # Check if URL is already in queue
        for i in range(self.url_queue.count()):
            if self.url_queue.item(i).text() == url:
                QMessageBox.information(self, "Duplicate URL", "This URL is already in the queue")
                return
        
        # Add URL to queue
        self.url_queue.addItem(url)
        self.url_input.clear()
        
        # Update queue label and enable buttons
        self.update_queue_label()
        self.clear_queue_btn.setEnabled(True)
        self.remove_url_btn.setEnabled(True)
    
    def remove_url_from_queue(self):
        selected_items = self.url_queue.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            row = self.url_queue.row(item)
            self.url_queue.takeItem(row)
        
        self.update_queue_label()
        
        # Disable buttons if queue is empty
        if self.url_queue.count() == 0:
            self.clear_queue_btn.setEnabled(False)
            self.remove_url_btn.setEnabled(False)
    
    def clear_queue(self):
        self.url_queue.clear()
        self.update_queue_label()
        self.clear_queue_btn.setEnabled(False)
        self.remove_url_btn.setEnabled(False)
    
    def update_queue_label(self):
        count = self.url_queue.count()
        self.url_queue_label.setText(f"Download Queue ({count} items)")
    
    def browse_output(self):
        # Start from the last used directory
        start_dir = self.settings.get_last_download_directory()
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", start_dir)
        if directory:
            self.output_path.setText(directory)
            # Save the new directory
            self.settings.set_last_download_directory(directory)
    
    def show_recent_directories(self):
        """Show a menu with recent directories"""
        recent_dirs = self.settings.get_recent_directories()
        
        if not recent_dirs:
            QMessageBox.information(self, "Recent Directories", "No recent directories found.")
            return
        
        # Create a menu with recent directories
        menu = QMenu(self)
        for directory in recent_dirs:
            # Show just the folder name and parent for readability
            display_name = f"{Path(directory).parent.name}/{Path(directory).name}"
            if len(display_name) > 50:
                display_name = "..." + display_name[-47:]
            
            action = QAction(f"📁 {display_name}", self)
            action.setToolTip(directory)  # Show full path on hover
            action.triggered.connect(lambda checked, d=directory: self.set_directory(d))
            menu.addAction(action)
        
        # Show the menu at the button position
        recent_btn = self.sender()
        if recent_btn:
            menu.exec_(recent_btn.mapToGlobal(recent_btn.rect().bottomLeft()))
    
    def set_quick_directory(self, directory):
        """Set a quick access directory"""
        if os.path.exists(directory):
            self.output_path.setText(directory)
            self.settings.set_last_download_directory(directory)
        else:
            # Try to create the directory
            try:
                os.makedirs(directory, exist_ok=True)
                self.output_path.setText(directory)
                self.settings.set_last_download_directory(directory)
            except Exception as e:
                QMessageBox.warning(self, "Directory Error", f"Could not access {directory}:\n{str(e)}")
    
    def set_directory(self, directory):
        """Set the output directory from recent directories"""
        if os.path.exists(directory):
            self.output_path.setText(directory)
            self.settings.set_last_download_directory(directory)
        else:
            reply = QMessageBox.question(self, "Directory Not Found", 
                                       f"Directory no longer exists:\n{directory}\n\nRemove from recent directories?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Remove from recent directories
                recent = self.settings.get_recent_directories()
                if directory in recent:
                    recent.remove(directory)
                    self.settings.set("recent_directories", recent)
    
    def apply_default_settings(self):
        """Apply saved default settings to UI controls"""
        try:
            defaults = self.settings.get_default_options()
            
            # Apply quality setting
            quality = defaults.get("quality", "best")
            index = self.quality_combo.findText(quality)
            if index >= 0:
                self.quality_combo.setCurrentIndex(index)
            
            # Apply audio quality setting
            audio_quality = defaults.get("audio_quality", "192")
            for i in range(self.audio_quality_combo.count()):
                if audio_quality in self.audio_quality_combo.itemText(i):
                    self.audio_quality_combo.setCurrentIndex(i)
                    break
            
            # Apply editor preference
            default_editor = defaults.get("default_editor", "premiere")
            if default_editor == "davinci":
                self.davinci_check.setChecked(True)
                self.premiere_check.setChecked(False)
            else:
                self.premiere_check.setChecked(True)
                self.davinci_check.setChecked(False)
            
            # Apply auto convert setting
            auto_convert = defaults.get("auto_convert", True)
            self.convert_check.setChecked(auto_convert)
            
            # Apply subtitle setting
            enable_subtitles = defaults.get("enable_subtitles", False)
            self.subtitle_check.setChecked(enable_subtitles)
            
        except Exception as e:
            print(f"Error applying default settings: {e}")
    
    def resizeEvent(self, event):
        """Handle window resize -- debounced to avoid excessive disk writes"""
        super().resizeEvent(event)
        if hasattr(self, '_resize_timer'):
            self._resize_timer.start()

    def _save_window_size(self):
        """Save window size after resize debounce"""
        if hasattr(self, 'settings'):
            self.settings.set_window_settings(self.width(), self.height())
    
    def closeEvent(self, event):
        """Handle window close to save settings and stop any running download"""
        # Check if a download is in progress
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            reply = QMessageBox.question(
                self, "Download in Progress",
                "A download is still running. Cancel and exit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.download_thread.request_stop()
            if not self.download_thread.wait(5000):
                # Graceful stop timed out, force terminate as last resort
                self.download_thread.terminate()
                self.download_thread.wait(2000)

        # Save current directory one more time
        current_dir = self.output_path.text().strip()
        if current_dir and os.path.exists(current_dir):
            self.settings.set_last_download_directory(current_dir)

        # Save window size
        self.settings.set_window_settings(self.width(), self.height())

        event.accept()
    
    def start_download(self):
        output_path = self.output_path.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Input Error", "Please select an output directory")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # AUTOMATIC OPTION MANAGEMENT - No more confusion!
        is_audio_mode = self.audio_radio.isChecked()
        is_video_mode = self.video_radio.isChecked()
        
        # Get options based on selected mode
        if is_audio_mode:
            # AUDIO MODE: Only audio-relevant options
            options = {
                'audio_only': True,
                'subtitle': False,  # Force disable - not needed for audio
                'quality': self.quality_combo.currentText(),
                'mp4': False,       # Force disable - we want MP3
                'premiere': False,  # Force disable - not relevant for audio
                'convert': False,   # Force disable - audio has its own conversion
            }
        else:
            # VIDEO MODE: Use actual checkbox values for user control
            options = {
                'audio_only': False,
                'subtitle': self.subtitle_check.isChecked(),
                'quality': self.quality_combo.currentText(),
                'mp4': True,        # Always enable MP4 for video
                'premiere': self.premiere_check.isChecked(),
                'davinci': self.davinci_check.isChecked(),
                'convert': self.convert_check.isChecked(),
            }
        
        # Add mode-specific options
        if is_audio_mode:
            # Audio-specific options
            quality_text = self.audio_quality_combo.currentText()
            if "192" in quality_text:
                options['audio_quality'] = '192'
            elif "128" in quality_text:
                options['audio_quality'] = '128'
            else:
                options['audio_quality'] = '96'
                
            # Add audio metadata options
            options['preserve_metadata'] = self.audio_metadata_check.isChecked()
            options['use_original_filename'] = self.audio_filename_check.isChecked()
        
        # Add format from advanced tab if specified (only for video mode)
        if is_video_mode and self.format_input.text().strip():
            options['format'] = self.format_input.text().strip()
        elif is_audio_mode:
            # For audio mode, ignore custom formats - we know what we want
            pass
            
        # Add platform-specific options
        platform = self.platform_combo.currentText()
        options['platform'] = platform
        
        # Show what mode we're in for clarity
        if is_audio_mode:
            self.status_label.setText("🎵 Ready to download audio (MP3)")
        else:
            self.status_label.setText("📹 Ready to download video (MP4)")
        
        if platform == "Instagram":
            options['instagram_no_login'] = self.instagram_no_login.isChecked()
        elif platform == "TikTok":
            # TikTok-specific options
            options['format'] = options.get('format') or "best"
        elif platform != "Auto-detect":
            # Default platform-specific options
            options['format'] = options.get('format') or "best"
        
        # Check if we're in batch mode
        if self.batch_check.isChecked():
            # Get URLs from queue
            urls = [self.url_queue.item(i).text() for i in range(self.url_queue.count())]
            if not urls:
                QMessageBox.warning(self, "Input Error", "Please add URLs to the queue")
                return
                
            # Start batch download
            self.start_batch_download(urls, output_path, options)
        else:
            # Single URL download
            url = self.url_input.text().strip()

            if not url:
                QMessageBox.warning(self, "Input Error", "Please enter a URL")
                return
                
            self.download_single_url(url, output_path, options)
    
    def start_batch_download(self, urls, output_path, options):
        """Start batch download process"""
        self.batch_urls = urls.copy()
        self.batch_output_path = output_path
        self.batch_options = options
        self.batch_current_index = 0
        self.batch_success_count = 0
        self.batch_fail_count = 0
        
        # Disable UI elements during batch download
        self.download_btn.setEnabled(False)
        self.batch_check.setEnabled(False)
        self.add_url_btn.setEnabled(False)
        self.remove_url_btn.setEnabled(False)
        self.clear_queue_btn.setEnabled(False)
        
        # Start first download
        self.download_next_in_batch()
    
    def download_single_url(self, url, output_path, options):
        """Download a single URL"""
        self.download_thread = DownloaderThread(url, output_path, options)
        self.download_thread.status.connect(self.update_status)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        
        self.download_btn.setEnabled(False)
        self.status_label.setText(f"Downloading: {url}")
        self.progress_bar.setValue(10)  # Show some initial progress
        self.download_thread.start()
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def update_progress(self, value):
        # Handle indeterminate progress (-1)
        if value == -1:
            # For indeterminate progress, we could animate the progress bar
            # But for now, just set it to a mid-range value
            self.progress_bar.setValue(50)
        else:
            self.progress_bar.setValue(value)
    
    def download_finished(self, success, message):
        self.status_label.setText(message)
        
        # Save download history and update directory if successful
        if success:
            output_path = self.output_path.text().strip()
            if output_path and os.path.exists(output_path):
                # Update last used directory
                self.settings.set_last_download_directory(output_path)
                
                # Save to download history
                if hasattr(self, 'batch_urls') and hasattr(self, 'batch_current_index'):
                    # Batch download - get current URL
                    if self.batch_current_index < len(self.batch_urls):
                        url = self.batch_urls[self.batch_current_index]
                    else:
                        url = "Batch download"
                else:
                    # Single download
                    url = self.url_input.text().strip()
                
                # Extract title from message if possible
                title = "Downloaded file"
                if "completed successfully:" in message:
                    try:
                        title = message.split("completed successfully:")[1].strip()
                    except (IndexError, AttributeError):
                        pass
                
                # Add to download history
                self.settings.add_download_history(url, title, output_path)
        
        # Check if we're in batch mode
        if hasattr(self, 'batch_urls') and self.batch_current_index < len(self.batch_urls):
            # Update batch statistics
            if success:
                self.batch_success_count += 1
            else:
                self.batch_fail_count += 1
            
            # Move to next URL in batch
            self.batch_current_index += 1
            # Reset progress bar for next download
            self.progress_bar.setValue(0)
            self.download_next_in_batch()
        else:
            # Single download or last in batch
            self.download_btn.setEnabled(True)
            # Ensure progress bar shows 100% for successful downloads
            if success:
                self.progress_bar.setValue(100)
            
            # Re-enable batch UI elements if needed
            if hasattr(self, 'batch_urls'):
                self.batch_check.setEnabled(True)
                self.add_url_btn.setEnabled(True)
                self.remove_url_btn.setEnabled(True)
                self.clear_queue_btn.setEnabled(True)
                
                # Show batch summary
                QMessageBox.information(self, "Batch Download Complete", 
                                      f"Completed {self.batch_current_index} downloads\n"
                                      f"Successful: {self.batch_success_count}\n"
                                      f"Failed: {self.batch_fail_count}")
                
                # Clean up batch attributes
                del self.batch_urls
                del self.batch_output_path
                del self.batch_options
                del self.batch_current_index
                del self.batch_success_count
                del self.batch_fail_count
            elif success:
                QMessageBox.information(self, "Success", "Download completed successfully!")
            else:
                QMessageBox.warning(self, "Error", message)
    
    def download_next_in_batch(self):
        """Download the next URL in the batch"""
        if self.batch_current_index < len(self.batch_urls):
            # Get the next URL
            url = self.batch_urls[self.batch_current_index]
            
            # Update status and highlight current item in queue
            self.status_label.setText(f"Downloading {self.batch_current_index + 1} of {len(self.batch_urls)}: {url}")
            self.url_queue.setCurrentRow(self.batch_current_index)
            
            # Start download
            self.download_single_url(url, self.batch_output_path, self.batch_options)
        else:
            # All downloads completed
            self.status_label.setText("Batch download completed")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
