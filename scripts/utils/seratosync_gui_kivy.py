#!/usr/bin/env python3
"""
Serato Sync GUI - Kivy Implementation
A modern cross-platform GUI for the Serato Sync application using Kivy and KivyMD.
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime

# Configure Kivy before other imports
from kivy.config import Config
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '700')  # Increased from default ~600 to 700

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.logger import Logger

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
# Platform-specific imports for toast
try:
    from kivymd.toast import toast
except TypeError:
    # Fallback for macOS - toast not supported on desktop
    def toast(message, duration=2.0):
        print(f"Toast: {message}")  # Simple fallback

# Add seratosync module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SeratoSyncGUI(MDApp):
    """Main GUI application class using KivyMD."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Darkorange"
        self.theme_cls.accent_palette = "Orange"
        
        # Configuration
        self.config = {}
        self.config_file = "config.json"
        
        # Dialog references
        self.file_manager = None
        self.current_field = None
        self.status_text = None
        
        # Database version check result
        self.db_version_result = None
        
    def build(self):
        """Build the main UI."""
        self.title = "Serato Sync - Modern GUI"
        
        # Main layout
        main_layout = MDBoxLayout(
            orientation="vertical", 
            spacing=dp(10), 
            padding=dp(20),
            md_bg_color=self.theme_cls.backgroundColor
        )
        
        # Add toolbar
        toolbar = MDTopAppBar(
            MDTopAppBarTitle(text="Serato Sync"),
            md_bg_color=self.theme_cls.primaryColor,
        )
        main_layout.add_widget(toolbar)
        
        # Create scroll view for content
        scroll = MDScrollView(
            md_bg_color=self.theme_cls.backgroundColor
        )
        content_layout = MDBoxLayout(
            orientation="vertical", 
            spacing=dp(15), 
            adaptive_height=True,
            padding=dp(10)
        )
        
        # Add sections
        content_layout.add_widget(self.create_config_section())
        content_layout.add_widget(self.create_operations_section())
        content_layout.add_widget(self.create_status_section())
        
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)
        
        # Load configuration
        Clock.schedule_once(lambda dt: self.load_config(), 0.5)
        
        # Show startup warning after build
        Clock.schedule_once(lambda dt: self.show_startup_warning(), 1.0)
        
        return main_layout
    
    def create_config_section(self):
        """Create configuration section."""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(300),
            elevation=3,
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=self.theme_cls.surfaceVariantColor,
            radius=[10, 10, 10, 10]
        )
        
        # Title
        title = MDLabel(
            text="Configuration",
            font_style="Title",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        card.add_widget(title)
        
        # Configuration fields
        config_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), adaptive_height=True)
        
        # Serato DB path
        self.serato_db_entry = MDTextField(
            hint_text="Path to Serato database directory (e.g., ~/Music/_Serato_)",
            size_hint_y=None,
            height=dp(60)
        )
        config_layout.add_widget(self.serato_db_entry)
        
        # Browse button for Serato DB
        browse_serato_btn = MDButton(
            MDButtonText(text="Browse Serato DB"),
            style="filled",
            size_hint_y=None,
            height=dp(36),
            on_release=lambda x: self.browse_for_directory("serato_db")
        )
        config_layout.add_widget(browse_serato_btn)
        
        # Music library path
        self.crates_path_entry = MDTextField(
            hint_text="Path to your Music Library folder (directory containing music files/folders to sync as crates)",
            size_hint_y=None,
            height=dp(60)
        )
        config_layout.add_widget(self.crates_path_entry)
        
        # Browse button for music library
        browse_crates_btn = MDButton(
            MDButtonText(text="Browse Music Library"),
            style="filled",
            size_hint_y=None,
            height=dp(36),
            on_release=lambda x: self.browse_for_directory("crates_path")
        )
        config_layout.add_widget(browse_crates_btn)
        
        card.add_widget(config_layout)
        return card
    
    def create_operations_section(self):
        """Create operations section."""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(250),
            elevation=3,
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=self.theme_cls.surfaceVariantColor,
            radius=[10, 10, 10, 10]
        )
        
        # Title
        title = MDLabel(
            text="Operations",
            font_style="Title",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        card.add_widget(title)
        
        # Operation buttons
        ops_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), adaptive_height=True)
        
        sync_btn = MDButton(
            MDButtonText(text="Sync Music Folders to Crates"),
            style="filled",
            size_hint_y=None,
            height=dp(40),
            on_release=lambda x: self.sync_library()
        )
        ops_layout.add_widget(sync_btn)
        
        report_btn = MDButton(
            MDButtonText(text="Generate Database Report"),
            style="filled",
            size_hint_y=None,
            height=dp(40),
            on_release=lambda x: self.generate_report()
        )
        ops_layout.add_widget(report_btn)
        
        cleanup_btn = MDButton(
            MDButtonText(text="Clean Database (Remove Duplicates & Corruption)"),
            style="filled",
            size_hint_y=None,
            height=dp(40),
            on_release=lambda x: self.clean_database()
        )
        ops_layout.add_widget(cleanup_btn)
        
        card.add_widget(ops_layout)
        return card
    
    def create_status_section(self):
        """Create status and logs section."""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(300),
            elevation=3,
            padding=dp(15),
            spacing=dp(10),
            md_bg_color=self.theme_cls.surfaceVariantColor,
            radius=[10, 10, 10, 10]
        )
        
        # Title
        title = MDLabel(
            text="Status & Logs",
            font_style="Title",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(40),
            bold=True
        )
        card.add_widget(title)
        
        # Status text area (using scrollable label)
        scroll_view = ScrollView()
        self.status_text = MDLabel(
            text="Serato Sync GUI initialized.\nReady for operations...",
            text_size=(None, None),
            theme_text_color="Secondary",
            font_name="RobotoMono-Regular",
            font_size="12sp",
            halign="left",
            valign="top"
        )
        scroll_view.add_widget(self.status_text)
        card.add_widget(scroll_view)
        
        return card
    
    def browse_for_directory(self, field_name):
        """Open file manager to browse for directory."""
        self.current_field = field_name
        
        if not self.file_manager:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_file_manager,
                select_path=self.select_path,
            )
        
        # Set initial path
        initial_path = "/"
        if field_name == "serato_db":
            # Try to find common Serato paths
            common_paths = [
                os.path.expanduser("~/Music/_Serato_"),
                os.path.expanduser("~/Documents/_Serato_"),
                os.path.expanduser("~/_Serato_")
            ]
            for path in common_paths:
                if os.path.exists(path):
                    initial_path = path
                    break
        elif field_name == "crates_path":
            # Try to find common music library paths
            common_paths = [
                os.path.expanduser("~/Music"),
                os.path.expanduser("~/Documents/Music"),
                os.path.expanduser("~/Desktop")
            ]
            for path in common_paths:
                if os.path.exists(path):
                    initial_path = path
                    break
        
        self.file_manager.show(initial_path)
    
    def select_path(self, path):
        """Handle path selection from file manager."""
        if self.current_field == "serato_db":
            self.serato_db_entry.text = path
        elif self.current_field == "crates_path":
            self.crates_path_entry.text = path
        
        self.exit_file_manager()
        field_description = "Serato database" if self.current_field == "serato_db" else "music library"
        self.log_message(f"Selected {field_description} path: {path}")
    
    def exit_file_manager(self, *args):
        """Close file manager."""
        if self.file_manager:
            self.file_manager.close()
    
    def show_startup_warning(self):
        """Show startup warning dialog."""
        def close_dialog(instance):
            self.dialog.dismiss()
            # Check database version after dialog
            self.check_database_version()
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Important Notice"),
            MDDialogSupportingText(
                text=(
                    "This application modifies your Serato database files. "
                    "Please ensure you have backed up your Serato library before proceeding.\n\n"
                    "The application will check your database version compatibility."
                )
            ),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="I UNDERSTAND"),
                    style="filled",
                    on_release=close_dialog
                ),
            ),
        )
        self.dialog.open()
    
    def check_database_version(self):
        """Check Serato database version compatibility."""
        def run_check():
            try:
                # Import seratosync modules
                from seratosync.database import read_database_v2_pfil_set
                
                serato_path = self.serato_db_entry.text.strip()
                if not serato_path:
                    self.db_version_result = "No Serato database path specified"
                    Clock.schedule_once(lambda dt: self.show_version_result(), 0)
                    return
                
                # Look for Database V2 file
                db_file = Path(serato_path) / "database V2"
                if not db_file.exists():
                    self.db_version_result = f"Database V2 file not found at: {db_file}"
                    Clock.schedule_once(lambda dt: self.show_version_result(), 0)
                    return
                
                # Try to read database to verify compatibility
                pfil_set, prefix, total_tracks = read_database_v2_pfil_set(db_file, 10)
                self.db_version_result = f"Database appears compatible! Found {total_tracks} tracks. Inferred prefix: {prefix or 'None'}"
                Clock.schedule_once(lambda dt: self.show_version_result(), 0)
                
            except Exception as e:
                self.db_version_result = f"Error checking database: {str(e)}"
                Clock.schedule_once(lambda dt: self.show_version_result(), 0)
        
        # Run check in background thread
        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
        self.log_message("Checking database version compatibility...")
    
    def show_version_result(self):
        """Show database version check result."""
        if not self.db_version_result:
            return
        
        # Determine if version is supported
        is_warning = "not supported" in self.db_version_result.lower() or "error" in self.db_version_result.lower()
        
        def close_version_dialog(instance):
            self.version_dialog.dismiss()
        
        self.version_dialog = MDDialog(
            MDDialogHeadlineText(text="Database Version Check"),
            MDDialogSupportingText(text=self.db_version_result),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    style="filled",
                    on_release=close_version_dialog
                ),
            ),
        )
        self.version_dialog.open()
        self.log_message(f"Database version check: {self.db_version_result}")
    
    def sync_library(self):
        """Sync library to crates."""
        def run_sync():
            try:
                self.log_message("Starting library sync operation...")
                
                # Import seratosync modules
                from seratosync.cli import main as seratosync_main
                
                serato_path = self.serato_db_entry.text.strip()
                crates_path = self.crates_path_entry.text.strip()
                
                if not serato_path or not os.path.exists(serato_path):
                    Clock.schedule_once(lambda dt: toast("Invalid Serato database path"), 0)
                    return
                
                if not crates_path or not os.path.exists(crates_path):
                    Clock.schedule_once(lambda dt: toast("Invalid music library directory path"), 0)
                    return
                
                # Build arguments for CLI
                db_file = Path(serato_path) / "database V2"
                subcrates_dir = Path(serato_path) / "Subcrates"
                
                args = [
                    "--db", str(db_file),
                    "--library-root", crates_path,
                    "--serato-root", str(serato_path)
                ]
                
                # Call the main CLI function
                result = seratosync_main(args)
                
                if result == 0:
                    Clock.schedule_once(lambda dt: self.log_message("Sync completed successfully!"), 0)
                    Clock.schedule_once(lambda dt: toast("Library sync completed successfully!"), 0)
                else:
                    Clock.schedule_once(lambda dt: self.log_message(f"Sync completed with warnings (exit code: {result})"), 0)
                    Clock.schedule_once(lambda dt: toast("Sync completed with warnings"), 0)
                
            except Exception as e:
                error_msg = f"Sync operation failed: {str(e)}"
                Clock.schedule_once(lambda dt: self.log_message(error_msg), 0)
                Clock.schedule_once(lambda dt: toast("Sync operation failed"), 0)
        
        # Run sync in background thread
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
    
    def generate_report(self):
        """Generate database report."""
        def run_report():
            try:
                self.log_message("Generating database report...")
                
                # Import seratosync modules
                from seratosync.database import read_database_v2_pfil_set
                from seratosync.library import scan_library, get_library_stats
                
                serato_path = self.serato_db_entry.text.strip()
                crates_path = self.crates_path_entry.text.strip()
                
                if not serato_path or not os.path.exists(serato_path):
                    Clock.schedule_once(lambda dt: toast("Invalid Serato database path"), 0)
                    return
                
                # Generate database statistics
                db_file = Path(serato_path) / "database V2"
                if db_file.exists():
                    pfil_set, prefix, total_tracks = read_database_v2_pfil_set(db_file)
                    report_lines = [
                        f"Database Report for: {serato_path}",
                        f"=" * 50,
                        f"Total tracks in database: {total_tracks}",
                        f"Inferred library prefix: {prefix or 'None'}",
                        f"Unique file paths: {len(pfil_set)}",
                    ]
                    
                    # Add library stats if path is specified
                    if crates_path and os.path.exists(crates_path):
                        library_map = scan_library(Path(crates_path))
                        dirs, files = get_library_stats(library_map)
                        report_lines.extend([
                            f"",
                            f"Music Library Directory: {crates_path}",
                            f"Audio directories: {dirs}",
                            f"Audio files found: {files}",
                        ])
                    
                    report = "\n".join(report_lines)
                else:
                    report = f"Database V2 file not found at: {db_file}"
                
                Clock.schedule_once(lambda dt: self.log_message(f"Report generated:\n{report}"), 0)
                Clock.schedule_once(lambda dt: toast("Database report generated successfully!"), 0)
                
            except Exception as e:
                error_msg = f"Report generation failed: {str(e)}"
                Clock.schedule_once(lambda dt: self.log_message(error_msg), 0)
                Clock.schedule_once(lambda dt: toast("Report generation failed"), 0)
        
        # Run report generation in background thread
        thread = threading.Thread(target=run_report, daemon=True)
        thread.start()
    
    def clean_database(self):
        """Clean database by removing duplicates and corrupted entries."""
        def show_cleanup_confirmation():
            def perform_cleanup(instance):
                self.cleanup_dialog.dismiss()
                self.run_database_cleanup()
            
            def cancel_cleanup(instance):
                self.cleanup_dialog.dismiss()
            
            self.cleanup_dialog = MDDialog(
                MDDialogHeadlineText(text="Database Cleanup Warning"),
                MDDialogSupportingText(
                    text=(
                        "This will clean your Serato database by:\n"
                        "• Removing duplicate tracks\n"
                        "• Removing corrupted entries\n"
                        "• Removing tracks without metadata\n\n"
                        "A backup will be created automatically.\n\n"
                        "This operation cannot be undone easily. Continue?"
                    )
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="CANCEL"),
                        style="outlined",
                        on_release=cancel_cleanup
                    ),
                    MDButton(
                        MDButtonText(text="CLEAN DATABASE"),
                        style="filled",
                        on_release=perform_cleanup
                    ),
                ),
            )
            self.cleanup_dialog.open()
        
        # Show confirmation dialog
        show_cleanup_confirmation()
    
    def run_database_cleanup(self):
        """Execute database cleanup in background thread."""
        def run_cleanup():
            try:
                self.log_message("Starting database cleanup operation...")
                
                serato_path = self.serato_db_entry.text.strip()
                if not serato_path or not os.path.exists(serato_path):
                    Clock.schedule_once(lambda dt: toast("Invalid Serato database path"), 0)
                    return
                
                db_file = Path(serato_path) / "database V2"
                if not db_file.exists():
                    Clock.schedule_once(lambda dt: toast("Database V2 file not found"), 0)
                    return
                
                # Import database functions
                from seratosync.database import read_database_v2_records, write_database_v2_records
                import database_cleanup
                
                # Read current database
                Clock.schedule_once(lambda dt: self.log_message("Reading database records..."), 0)
                records = read_database_v2_records(db_file)
                
                # Analyze before cleanup
                Clock.schedule_once(lambda dt: self.log_message("Analyzing database for issues..."), 0)
                analysis = database_cleanup.analyze_database_issues(records)
                
                analysis_msg = (
                    f"Database analysis:\n"
                    f"  Total records: {analysis['total_records']}\n"
                    f"  Without file path: {analysis['records_without_path']}\n"
                    f"  Without metadata: {analysis['records_without_metadata']}\n"
                    f"  Potential duplicates: {analysis['potential_duplicates']}\n"
                    f"  Corrupted paths: {analysis['corrupted_paths']}"
                )
                Clock.schedule_once(lambda dt: self.log_message(analysis_msg), 0)
                
                # Create backup
                Clock.schedule_once(lambda dt: self.log_message("Creating database backup..."), 0)
                backup_path = database_cleanup.backup_database(db_file)
                Clock.schedule_once(lambda dt: self.log_message(f"Backup saved: {backup_path.name}"), 0)
                
                # Clean records
                Clock.schedule_once(lambda dt: self.log_message("Cleaning database records..."), 0)
                cleaned_records, stats = database_cleanup.clean_database_records(
                    records,
                    remove_duplicates=True,
                    require_metadata=True
                )
                
                # Write cleaned database
                Clock.schedule_once(lambda dt: self.log_message("Writing cleaned database..."), 0)
                write_database_v2_records(db_file, cleaned_records)
                
                # Report results
                results_msg = (
                    f"Database cleanup completed!\n"
                    f"  Original records: {stats['original_count']}\n"
                    f"  Removed (no path): {stats['removed_no_path']}\n"
                    f"  Removed (no metadata): {stats['removed_no_metadata']}\n"
                    f"  Removed (duplicates): {stats['removed_duplicates']}\n"
                    f"  Removed (corrupted): {stats['removed_corrupted']}\n"
                    f"  Final records: {stats['final_count']}\n"
                    f"  Records saved: {stats['final_count'] - stats['original_count']}"
                )
                Clock.schedule_once(lambda dt: self.log_message(results_msg), 0)
                Clock.schedule_once(lambda dt: toast(f"Database cleaned! {stats['final_count']} tracks remaining"), 0)
                
            except Exception as e:
                error_msg = f"Database cleanup failed: {str(e)}"
                Clock.schedule_once(lambda dt: self.log_message(error_msg), 0)
                Clock.schedule_once(lambda dt: toast("Database cleanup failed"), 0)
        
        # Run cleanup in background thread
        thread = threading.Thread(target=run_cleanup, daemon=True)
        thread.start()
    
    def log_message(self, message):
        """Add message to status log."""
        if not self.status_text:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Update status text
        current_text = self.status_text.text
        if current_text == "Serato Sync GUI initialized.\nReady for operations...":
            self.status_text.text = formatted_message
        else:
            self.status_text.text = current_text + "\n" + formatted_message
        
        # Adjust text size for wrapping
        self.status_text.text_size = (self.status_text.parent.width - dp(20), None)
        
        Logger.info(f"SeratoSync: {message}")
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                
                # Update UI fields
                if 'serato_db_path' in self.config:
                    self.serato_db_entry.text = self.config['serato_db_path']
                if 'music_library_path' in self.config:
                    self.crates_path_entry.text = self.config['music_library_path']
                elif 'crates_path' in self.config:  # Backward compatibility
                    self.crates_path_entry.text = self.config['crates_path']
                
                self.log_message("Configuration loaded successfully!")
            else:
                self.log_message("No existing configuration found. Using defaults.")
                
        except Exception as e:
            self.log_message(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            self.config.update({
                'serato_db_path': self.serato_db_entry.text.strip(),
                'music_library_path': self.crates_path_entry.text.strip(),
            })
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.log_message("Configuration saved successfully!")
            
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
    
    def on_stop(self):
        """Called when the app is closing."""
        # Save configuration on exit
        if hasattr(self, 'serato_db_entry') and hasattr(self, 'crates_path_entry'):
            self.save_config()


def main():
    """Main entry point."""
    try:
        app = SeratoSyncGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
