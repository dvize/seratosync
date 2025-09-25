#!/usr/bin/env python3
"""
Serato Sync GUI Application

A modern cross-platform GUI for managing Serato sync configuration and operations.
Built with CustomTkinter for a modern appearance on Windows and macOS.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import json
import sys
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import time
import datetime


class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tipwindow = None

    def enter(self, event=None):
        self.show_tooltip()

    def leave(self, event=None):
        self.hide_tooltip()

    def show_tooltip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background='#ffffe0', relief='solid', borderwidth=1,
                        font=('Arial', '10', 'normal'), wraplength=300)
        label.pack(ipadx=1)

    def hide_tooltip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def detect_database_version(db_path: str) -> tuple[bool, str]:
    """
    Detect if the database is Serato V2 format.
    Returns (is_v2, version_info)
    """
    try:
        if not os.path.exists(db_path):
            return False, "Database file not found"
            
        with open(db_path, 'rb') as f:
            # Read more bytes to ensure we catch the version string
            header = f.read(200)
            
        # Check for V2 format indicators directly in bytes first
        if b'2.0/Serato Scratch LIVE Database' in header:
            return True, "Serato Database V2 (Compatible)"
            
        # Check for UTF-16LE encoded V2 signature (common in newer Serato versions)
        # Use a shorter signature that should be contained within our header read
        v2_signature_utf16 = '2.0/Serato Scratch LIVE Databa'.encode('utf-16le')
        if v2_signature_utf16 in header:
            return True, "Serato Database V2 (Compatible)"
            
        # Check for legacy patterns
        if b'Serato ScratchLive database' in header:
            return False, "Legacy Serato Database (V1 - INCOMPATIBLE)"
            
        # Check for UTF-16LE encoded legacy signature
        legacy_signature_utf16 = 'Serato ScratchLive database'.encode('utf-16le')
        if legacy_signature_utf16 in header:
            return False, "Legacy Serato Database (V1 - INCOMPATIBLE)"
            
        # Check for any database-related content (case insensitive)
        if b'database' in header.lower() or 'database'.encode('utf-16le') in header:
            return False, "Unknown Serato Database Format (Possibly Legacy - INCOMPATIBLE)"
        else:
            return False, "Not a recognized Serato database file"
            
    except Exception as e:
        return False, f"Error reading database: {str(e)}"


# Set appearance mode and color theme
ctk.set_appearance_mode("system")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green


class SeratoSyncGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Serato Sync V2 ONLY - Configuration & Operations")
        self.root.geometry("950x900")
        self.root.minsize(900, 850)
        
        # Configuration data
        self.config_data = {}
        self.config_file_path = "config.json"
        
        # Show critical startup warning
        self.show_startup_warning()
        
        # Setup UI
        self.setup_ui()
        self.load_config()
        
    def show_startup_warning(self):
        """Show critical compatibility warning at startup."""
        response = messagebox.askyesno(
            "⚠️ CRITICAL: Serato V2 Compatibility Warning ⚠️",
            "🚫 DANGER: This application is ONLY for Serato V2 databases! 🚫\n\n"
            "✅ COMPATIBLE WITH:\n"
            "• Serato V2 (New Beta Version)\n"
            "• Modern Serato installations\n\n"
            "🚫 NOT COMPATIBLE WITH:\n"
            "• Legacy Serato databases\n"
            "• Older Serato versions\n"
            "• Non-V2 database formats\n\n"
            "⚠️ WARNING: Using this tool with incompatible databases will:\n"
            "• Completely corrupt your music library\n"
            "• Destroy all playlists and crates\n"
            "• Cause irreversible data loss\n\n"
            "🔒 SAFETY FEATURES:\n"
            "• Automatic database version detection\n"
            "• Blocking of incompatible operations\n"
            "• Multiple confirmation dialogs\n\n"
            "Do you understand these risks and confirm you are using Serato V2?"
        )
        
        if not response:
            messagebox.showinfo("Application Cancelled", 
                              "Application closed for safety.\n\n"
                              "Only proceed if you are certain you have Serato V2 (new beta).")
            sys.exit(0)
        
    def setup_ui(self):
        """Setup the main UI components."""
        
        # Main frame with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Serato Sync Configuration (V2 ONLY)", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 8))
        
        # Compatibility warning
        warning_label = ctk.CTkLabel(
            main_frame, 
            text="⚠️ WARNING: Only compatible with Serato V2 databases (new beta) ⚠️", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e74c3c"
        )
        warning_label.pack(pady=(0, 15))
        
        # Configuration section
        self.setup_config_section(main_frame)
        
        # Operations section
        self.setup_operations_section(main_frame)
        
        # Status section
        self.setup_status_section(main_frame)
        
    def setup_config_section(self, parent):
        """Setup the configuration section."""
        
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        config_title = ctk.CTkLabel(
            config_frame, 
            text="Configuration Settings", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        config_title.pack(pady=(15, 10))
        
        # Config fields frame
        fields_frame = ctk.CTkFrame(config_frame)
        fields_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Library root path
        lib_entry = self.setup_path_field(
            fields_frame, 
            "Music Library Root:", 
            "library_root", 
            "Select music library root directory"
        )
        ToolTip(lib_entry, "The top-level folder containing your music files.\nThis is where seratosync will scan for tracks to organize into crates.")
        
        # Serato root path
        serato_entry = self.setup_path_field(
            fields_frame, 
            "Serato Root Directory:", 
            "serato_root", 
            "Select _Serato_ directory"
        )
        ToolTip(serato_entry, "Your Serato installation directory (usually named '_Serato_').\nContains your Database V2, crate files, and other Serato data.")
        
        # Extensions field
        ext_entry = self.setup_text_field(
            fields_frame,
            "Audio Extensions:",
            "exts",
            "Comma-separated: .mp3,.m4a,.aac,.flac,.wav"
        )
        ToolTip(ext_entry, "File extensions to include when scanning your music library.\nSeparate multiple extensions with commas (e.g., .mp3,.aac,.flac,.m4a)")
        
        # Config file operations
        config_ops_frame = ctk.CTkFrame(config_frame)
        config_ops_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            config_ops_frame,
            text="Save Configuration",
            command=self.save_config,
            height=30,
            font=ctk.CTkFont(size=12)
        ).pack(pady=8)
        
    def setup_path_field(self, parent, label_text, config_key, dialog_title, file_mode=False):
        """Setup a path input field with browse button."""
        
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)
        
        # Label
        label = ctk.CTkLabel(row_frame, text=label_text, width=180, anchor="w", font=ctk.CTkFont(size=12))
        label.pack(side="left", padx=(8, 4))
        
        # Entry
        entry = ctk.CTkEntry(row_frame, height=28, font=ctk.CTkFont(size=11))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        # Browse button
        def browse_callback():
            if file_mode:
                path = filedialog.askopenfilename(
                    title=dialog_title,
                    filetypes=[("Database files", "*"), ("All files", "*.*")]
                )
            else:
                path = filedialog.askdirectory(title=dialog_title)
                
            if path:
                entry.delete(0, tk.END)
                entry.insert(0, path)
        
        browse_btn = ctk.CTkButton(
            row_frame,
            text="Browse",
            command=browse_callback,
            width=70,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        browse_btn.pack(side="right", padx=(0, 8))
        
        # Store reference to entry widget
        setattr(self, f"{config_key}_entry", entry)
        return entry
        
    def setup_text_field(self, parent, label_text, config_key, placeholder_text=""):
        """Setup a text input field."""
        
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=3)
        
        # Label
        label = ctk.CTkLabel(row_frame, text=label_text, width=180, anchor="w", font=ctk.CTkFont(size=12))
        label.pack(side="left", padx=(8, 4))
        
        # Entry
        entry = ctk.CTkEntry(row_frame, placeholder_text=placeholder_text, height=28, font=ctk.CTkFont(size=11))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # Store reference to entry widget
        setattr(self, f"{config_key}_entry", entry)
        return entry
        
    def setup_operations_section(self, parent):
        """Setup the operations sections."""
        
        # Preview Changes section
        self.setup_preview_section(parent)
        
        # Database Operations section
        self.setup_database_section(parent)
        
    def setup_preview_section(self, parent):
        """Setup the preview changes section."""
        
        preview_frame = ctk.CTkFrame(parent)
        preview_frame.pack(fill="x", pady=(0, 8))
        
        # Section title
        preview_title = ctk.CTkLabel(
            preview_frame, 
            text="Preview Changes", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        preview_title.pack(pady=(15, 10))
        
        # Preview button
        preview_buttons_frame = ctk.CTkFrame(preview_frame)
        preview_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        dry_run_btn = ctk.CTkButton(
            preview_buttons_frame,
            text="👀 Dry Run (Preview Changes)",
            command=self.run_dry_run,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        dry_run_btn.pack(fill="x", pady=8)
        ToolTip(dry_run_btn, "Preview what changes will be made without modifying any files.\nCompletely safe - shows you exactly what would happen.")
        
    def setup_database_section(self, parent):
        """Setup the database operations section."""
        
        db_frame = ctk.CTkFrame(parent)
        db_frame.pack(fill="x", pady=(0, 15))
        
        # Section title
        db_title = ctk.CTkLabel(
            db_frame, 
            text="Database Operations", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        db_title.pack(pady=(15, 10))
        
        # Database operations buttons
        db_buttons_frame = ctk.CTkFrame(db_frame)
        db_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Backup and Restore row
        backup_row_frame = ctk.CTkFrame(db_buttons_frame, fg_color="transparent")
        backup_row_frame.pack(fill="x", pady=(8, 4))
        
        backup_btn = ctk.CTkButton(
            backup_row_frame,
            text="🔒 Backup Database V2",
            command=self.backup_database,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        backup_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ToolTip(backup_btn, "Create a timestamped backup of your Serato Database V2 file.\nRecommended before making any database changes.")
        
        restore_btn = ctk.CTkButton(
            backup_row_frame,
            text="🔓 Restore Database V2", 
            command=self.restore_database,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        restore_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ToolTip(restore_btn, "Restore your Database V2 from a previous backup file.\nUse this to undo changes or recover from issues.")
        
        # Update Database row
        update_row_frame = ctk.CTkFrame(db_buttons_frame, fg_color="transparent")
        update_row_frame.pack(fill="x", pady=(4, 8))
        
        update_db_btn = ctk.CTkButton(
            update_row_frame,
            text="🎵 Update Database V2 (Add New Tracks)",
            command=self.update_database,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#e74c3c",  # Red color for important operation
            hover_color="#c0392b"
        )
        update_db_btn.pack(fill="x")
        ToolTip(update_db_btn, "Add new tracks from your library to Serato's Database V2.\n⚠️ MODIFIES DATABASE V2 - Creates automatic backup first!\nClose Serato before using this operation.")
        
    def setup_status_section(self, parent):
        """Setup the status/log section."""
        
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="both", expand=True)
        
        # Section title
        status_title = ctk.CTkLabel(
            status_frame, 
            text="Operation Log", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.pack(pady=(15, 8))
        
        # Log text area
        self.log_text = ctk.CTkTextbox(
            status_frame,
            height=180,
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Clear log button
        ctk.CTkButton(
            status_frame,
            text="Clear Log",
            command=self.clear_log,
            width=90,
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(pady=(0, 15))
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Update the GUI
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.delete("1.0", tk.END)
        
    def load_config(self):
        """Load configuration from config.json file."""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r') as f:
                    self.config_data = json.load(f)
                self.populate_fields()
                self.log_message(f"Configuration loaded from {self.config_file_path}")
            else:
                self.log_message("No config file found, using defaults")
        except Exception as e:
            self.log_message(f"Error loading config: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to load configuration:\n{str(e)}")
            
    def populate_fields(self):
        """Populate UI fields with loaded configuration."""
        # Clear all fields first
        self.library_root_entry.delete(0, tk.END)
        self.serato_root_entry.delete(0, tk.END)
        self.exts_entry.delete(0, tk.END)
        
        # Populate from config data with cross-platform path normalization
        if 'library_root' in self.config_data:
            # Normalize path for display while preserving cross-platform compatibility
            path_value = str(Path(self.config_data['library_root']))
            self.library_root_entry.insert(0, path_value)
            
        if 'serato_root' in self.config_data:
            # Normalize path for display while preserving cross-platform compatibility  
            path_value = str(Path(self.config_data['serato_root']))
            self.serato_root_entry.insert(0, path_value)
            
        # Extensions with default fallback including .aac for CLI compatibility
        if 'exts' in self.config_data:
            self.exts_entry.insert(0, str(self.config_data['exts']))
        else:
            self.exts_entry.insert(0, ".mp3,.m4a,.aac,.flac,.wav")
                
    def save_config(self):
        """Save current configuration to config.json file."""
        try:
            # Collect current values from UI and normalize paths for cross-platform compatibility
            library_root = self.library_root_entry.get().strip()
            serato_root = self.serato_root_entry.get().strip()
            
            # Use pathlib.Path for cross-platform compatibility, then convert to string
            # This ensures consistent behavior on Windows, macOS, and Linux
            if library_root:
                library_root = str(Path(library_root))
            if serato_root:
                serato_root = str(Path(serato_root))
            
            # Auto-generate database path from serato_root using pathlib
            db_path = ""
            if serato_root:
                db_path = str(Path(serato_root) / "database V2")
                
            # Get extensions
            extensions = self.exts_entry.get().strip()
            if not extensions:
                extensions = ".mp3,.m4a,.aac,.flac,.wav"  # Default with .aac for compatibility
            
            # Create config in the same order as the original script format
            self.config_data = {
                'db': db_path,
                'library_root': library_root,
                'serato_root': serato_root,
                'exts': extensions
            }
            
            # Save to file
            with open(self.config_file_path, 'w') as f:
                json.dump(self.config_data, f, indent=2)
                
            self.log_message(f"Configuration saved to {self.config_file_path}")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            self.log_message(f"Error saving config: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")
            
    def validate_basic_config(self) -> bool:
        """Validate basic configuration fields without database version checking."""
        required_fields = {
            'serato_root': self.serato_root_entry.get().strip()
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                messagebox.showerror("Configuration Error", f"Please set the {field_name.replace('_', ' ').title()} field")
                return False
                
            if not os.path.exists(field_value):
                messagebox.showerror("Path Error", f"Path does not exist: {field_value}")
                return False
        
        # Validate that Serato root contains the expected structure
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        if not os.path.exists(db_path):
            messagebox.showerror("Serato Structure Error", 
                               f"Could not find 'database V2' file in Serato directory:\n{serato_root}\n\n"
                               f"Please ensure you selected the correct _Serato_ directory.")
            return False
                
        return True
            
    def validate_config(self) -> bool:
        """Validate that required configuration fields are set."""
        required_fields = {
            'library_root': self.library_root_entry.get().strip(), 
            'serato_root': self.serato_root_entry.get().strip()
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                messagebox.showerror("Configuration Error", f"Please set the {field_name.replace('_', ' ').title()} field")
                return False
                
            if not os.path.exists(field_value):
                messagebox.showerror("Path Error", f"Path does not exist: {field_value}")
                return False
        
        # Validate that Serato root contains the expected structure
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        if not os.path.exists(db_path):
            messagebox.showerror("Serato Structure Error", 
                               f"Could not find 'database V2' file in Serato directory:\n{serato_root}\n\n"
                               f"Please ensure you selected the correct _Serato_ directory.")
            return False
        
        # CRITICAL: Check database version compatibility
        is_v2, version_info = detect_database_version(db_path)
        if not is_v2:
            messagebox.showerror("⚠️ INCOMPATIBLE DATABASE VERSION ⚠️", 
                               f"DANGER: {version_info}\n\n"
                               f"🚫 This application is ONLY compatible with Serato V2 databases!\n\n"
                               f"Using this tool with legacy Serato databases will cause:\n"
                               f"• Complete database corruption\n"
                               f"• Loss of all your tracks and playlists\n"
                               f"• Irreversible damage to your Serato library\n\n"
                               f"⚠️ DO NOT PROCEED unless you are using Serato V2 (new beta)!\n\n"
                               f"Database: {db_path}\n"
                               f"Status: {version_info}")
            return False
        
        # Show confirmation for V2 databases
        self.log_message(f"✅ Database version check passed: {version_info}")
                
        return True
        
    def run_seratosync_command(self, args: list, description: str):
        """Run seratosync command in a separate thread."""
        def run_command():
            try:
                self.log_message(f"Starting: {description}")
                self.log_message("-" * 50)
                
                # Save current config before running
                self.save_config()
                
                # Build command with config file
                config_path = os.path.abspath(self.config_file_path)
                cmd = [sys.executable, "-m", "seratosync", "--config", config_path] + args
                
                self.log_message(f"Running: {' '.join(cmd)}")
                self.log_message("-" * 50)
                
                # Run command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                # Log output
                if result.stdout:
                    self.log_message("STDOUT:")
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log_message(f"  {line.strip()}")
                        else:
                            self.log_message("")  # Preserve empty lines
                            
                if result.stderr:
                    self.log_message("STDERR:")
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self.log_message(f"  {line.strip()}", "ERROR")
                
                self.log_message("-" * 50)
                if result.returncode == 0:
                    self.log_message(f"✅ {description} completed successfully")
                else:
                    self.log_message(f"❌ {description} failed with exit code {result.returncode}", "ERROR")
                    if not result.stdout and not result.stderr:
                        self.log_message("No output captured. The command may have run silently or failed to start.", "ERROR")
                    
            except Exception as e:
                self.log_message(f"❌ Error running {description}: {str(e)}", "ERROR")
                
        # Run in thread to prevent UI freezing
        threading.Thread(target=run_command, daemon=True).start()
        
    def backup_database(self):
        """Create a backup of the Database V2 file."""
        if not self.validate_basic_config():
            return
        
        # Auto-detect database path from Serato root
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        
        # Create timestamp with current local time
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        
        try:
            self.log_message(f"Creating backup at {now.strftime('%Y-%m-%d %I:%M:%S %p')}...")
            shutil.copy2(db_path, backup_path)
            self.log_message(f"✅ Database backed up to: {backup_path}")
            messagebox.showinfo("Backup Complete", f"Database backed up to:\n{backup_path}\n\nCreated: {now.strftime('%Y-%m-%d %I:%M:%S %p')}")
        except Exception as e:
            self.log_message(f"❌ Backup failed: {str(e)}", "ERROR")
            messagebox.showerror("Backup Failed", f"Failed to backup database:\n{str(e)}")
            
    def restore_database(self):
        """Restore Database V2 from a backup file."""
        backup_path = filedialog.askopenfilename(
            title="Select Database V2 Backup File",
            filetypes=[("All files", "*.*"), ("Backup files", "*.backup_*")]
        )
        
        if not backup_path:
            return
            
        if not self.validate_basic_config():
            return
        
        # Auto-detect database path from Serato root
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        
        if messagebox.askyesno("Restore Database", 
                              f"This will replace your current Database V2 with the backup.\n\n"
                              f"Current: {db_path}\n"
                              f"Backup: {backup_path}\n\n"
                              f"Are you sure you want to continue?"):
            try:
                shutil.copy2(backup_path, db_path)
                self.log_message(f"✅ Database restored from: {backup_path}")
                messagebox.showinfo("Restore Complete", "Database restored successfully!")
            except Exception as e:
                self.log_message(f"❌ Restore failed: {str(e)}", "ERROR")
                messagebox.showerror("Restore Failed", f"Failed to restore database:\n{str(e)}")
                
    def validate_basic_config(self) -> bool:
        """Basic validation without database version checking (for dry run)."""
        required_fields = {
            'library_root': self.library_root_entry.get().strip(), 
            'serato_root': self.serato_root_entry.get().strip()
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                messagebox.showerror("Configuration Error", f"Please set the {field_name.replace('_', ' ').title()} field")
                return False
                
            if not os.path.exists(field_value):
                messagebox.showerror("Path Error", f"Path does not exist: {field_value}")
                return False
        
        # Basic check for Serato directory structure (no version validation)
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        if not os.path.exists(db_path):
            messagebox.showerror("Serato Structure Error", 
                               f"Could not find 'database V2' file in Serato directory:\n{serato_root}\n\n"
                               f"Please ensure you selected the correct _Serato_ directory.")
            return False
                
        return True

    def run_dry_run(self):
        """Run seratosync in dry-run mode to preview changes."""
        if not self.validate_basic_config():
            return
        
        # Clear the log to show fresh output
        self.log_text.delete("1.0", tk.END)
        self.log_message("Starting dry run preview...")
        
        # Run dry run command
        self.run_seratosync_command(["--dry-run"], "Dry run preview")
        
    def update_database(self):
        """Update Database V2 with new tracks."""
        if not self.validate_config():
            return
        
        # Double-check database version before any modifications
        serato_root = self.serato_root_entry.get().strip()
        db_path = os.path.join(serato_root, "database V2")
        is_v2, version_info = detect_database_version(db_path)
        
        if not is_v2:
            messagebox.showerror("🚫 DATABASE MODIFICATION BLOCKED 🚫", 
                               f"CRITICAL SAFETY CHECK FAILED!\n\n"
                               f"Database: {version_info}\n\n"
                               f"🛑 This operation has been BLOCKED to prevent data corruption.\n\n"
                               f"This application can ONLY modify Serato V2 databases.\n"
                               f"Attempting to modify legacy databases will result in:\n"
                               f"• Complete loss of your music library\n"
                               f"• Irreversible corruption of all playlists\n"
                               f"• Total destruction of Serato data\n\n"
                               f"Please ensure you are using Serato V2 (new beta) before proceeding.")
            return
            
        # Final confirmation with extra warnings
        if messagebox.askyesno("⚠️ FINAL WARNING: Modify Database V2 ⚠️", 
                              f"🔥 LAST CHANCE TO CANCEL 🔥\n\n"
                              f"Database verified as: {version_info}\n\n"
                              f"This operation will PERMANENTLY modify your database:\n"
                              f"• Create automatic backup first\n"
                              f"• Add new tracks found in your library\n"
                              f"• Update relevant crates\n\n"
                              f"⚠️ REQUIREMENTS:\n"
                              f"• Serato MUST be completely closed\n"
                              f"• You have confirmed this is Serato V2\n"
                              f"• You understand this modifies your database\n\n"
                              f"Proceed with database modification?"):
            self.run_seratosync_command(["--update-db"], "Update Database V2")
            
    def run(self):
        """Start the GUI application."""
        self.log_message("Serato Sync GUI started")
        self.log_message("Load your configuration and select an operation")
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    app = SeratoSyncGUI()
    app.run()


if __name__ == "__main__":
    main()
