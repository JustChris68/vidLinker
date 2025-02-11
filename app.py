import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import traceback
from typing import Optional, Dict, List
from settings import Settings
from obs_manager import OBSManager
from vdo_ninja_manager import VDONinjaManager
from ui_components import SettingsDialog, ScrollableFrame
import datetime
import logging

class PlayerFrame(ttk.Frame):
    def __init__(self, parent, player_num, initial_name="", initial_char="", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.player_num = player_num
        
        # Player info frame
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", expand=True, padx=5, pady=2)
        
        # Player number label
        ttk.Label(info_frame, text=f"Player {player_num}:").pack(side="left", padx=(0,5))
        
        # Player name entry
        self.name_var = tk.StringVar(value=initial_name)
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(name_frame, text="Name:").pack(side="left", padx=(0,5))
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side="left", fill="x", expand=True)
        
        # Character name entry
        self.char_var = tk.StringVar(value=initial_char)
        char_frame = ttk.Frame(info_frame)
        char_frame.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Label(char_frame, text="Character:").pack(side="left", padx=(0,5))
        ttk.Entry(char_frame, textvariable=self.char_var).pack(side="left", fill="x", expand=True)
        
        # Delete button
        self.delete_button = ttk.Button(info_frame, text="Delete", command=self.on_delete)
        self.delete_button.pack(side="right", padx=5)
        
        # Callback for deletion
        self.on_delete_callback = None
    
    def get_player_info(self):
        return {
            "name": self.name_var.get(),
            "character": self.char_var.get()
        }
    
    def set_delete_callback(self, callback):
        self.on_delete_callback = callback
    
    def on_delete(self):
        if self.on_delete_callback:
            self.on_delete_callback(self)

class RoomConfigFrame(ttk.LabelFrame):
    """Frame for room configuration"""
    def __init__(self, parent, app):
        super().__init__(parent, text="Room Configuration")
        self.app = app
        
        # Room name
        name_frame = ttk.Frame(self)
        name_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(name_frame, text="Room Name:").pack(side="left", padx=2)
        self.room_name = ttk.Entry(name_frame)
        self.room_name.pack(side="left", expand=True, fill="x", padx=2)
        
        # Room password
        pass_frame = ttk.Frame(self)
        pass_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(pass_frame, text="Password:").pack(side="left", padx=2)
        self.room_password = ttk.Entry(pass_frame)
        self.room_password.pack(side="left", expand=True, fill="x", padx=2)
        
        # Password inclusion checkbox
        self.include_password = tk.BooleanVar(value=False)
        self.password_checkbox = ttk.Checkbutton(pass_frame, text="Include in links", 
                                               variable=self.include_password,
                                               command=self.on_password_change)
        self.password_checkbox.pack(side="right", padx=5)
        
        # Room control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=2)
        
        # Left side buttons
        left_buttons = ttk.Frame(btn_frame)
        left_buttons.pack(side="left", fill="x")
        
        ttk.Button(left_buttons, text="New Room", 
                  command=self.new_room).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Save Room",
                  command=self.app.save_room).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Load Room",
                  command=self.app.load_room_dialog).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Documentation",
                  command=self.app.show_documentation).pack(side="left", padx=5)
        ttk.Button(left_buttons, text="Settings",
                  command=self.app.show_settings).pack(side="left", padx=5)
        
        # Bind events
        self.room_name.bind('<KeyRelease>', self.on_field_change)
        self.room_password.bind('<KeyRelease>', self.on_password_change)
    
    def new_room(self):
        """Create a new room"""
        self.room_name.delete(0, "end")
        self.room_password.delete(0, "end")
        
        # Clear existing players
        if hasattr(self.app, 'player_entries'):
            for entry in self.app.player_entries:
                entry['frame'].destroy()
            self.app.player_entries.clear()
        
        # Trigger link generation
        self.app.generate_links()
    
    def on_field_change(self, event=None):
        """Handle field changes"""
        if hasattr(self.app, 'generate_links'):
            self.app.generate_links()
    
    def on_password_change(self, event=None):
        """Handle password field changes"""
        # Update checkbox state based on password field
        if not self.room_password.get().strip():
            self.include_password.set(False)
        
        # Trigger link update
        if hasattr(self.app, 'generate_links'):
            self.app.generate_links()
    
    def get_room_name(self):
        """Get current room name"""
        return self.room_name.get().strip()
    
    def get_room_password(self):
        """Get current room password if inclusion is enabled"""
        if self.include_password.get() and self.room_password.get().strip():
            return self.room_password.get().strip()
        return ""
    
    def set_room_name(self, name):
        """Set room name"""
        self.room_name.delete(0, "end")
        self.room_name.insert(0, name or "")
    
    def set_room_password(self, password):
        """Set room password"""
        self.room_password.delete(0, "end")
        self.room_password.insert(0, password or "")

class App:
    def __init__(self):
        """Initialize the application"""
        self.root = tk.Tk()
        self.root.title("VDO.Ninja Link Manager")
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill="both", expand=True)
        
        # Initialize logging
        self.debug_log_path = "obs_debug.log"
        logging.basicConfig(
            filename=self.debug_log_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load settings
        self.settings = Settings()
        self.settings.load()
        
        # Create UI components
        self.create_room_config_frame()
        self.create_player_list_frame()
        self.create_debug_frame()
        
        # Update window size to fit content
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        
        # Add 10% padding
        width = int(width * 1.1)
        height = int(height * 1.1)
        
        # Center window
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        # Set window size and position
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Initialize OBS manager
        self.obs_manager = OBSManager()
        if self.settings.interface.enable_obs:
            self.connect_to_obs()
        
        # Initialize VDO.Ninja manager
        self.vdo_ninja = VDONinjaManager()
        
        # Load initial room config if exists
        if self.settings.room and self.settings.room.room_name:
            self.room_config.set_room_name(self.settings.room.room_name)
            self.room_config.set_room_password(self.settings.room.room_password)
            self.generate_links()
            
    def create_room_config_frame(self):
        """Create the room configuration frame"""
        # Create frame
        self.room_config = RoomConfigFrame(self.main_frame, self)
        self.room_config.pack(fill="x", padx=5, pady=5)
        
    def create_player_list_frame(self):
        """Create the player list frame"""
        # Create frame
        self.player_list_frame = ttk.LabelFrame(self.main_frame, text="Players")
        self.player_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Create control buttons frame at top
        control_frame = ttk.Frame(self.player_list_frame)
        control_frame.pack(fill="x", padx=5, pady=2)
        
        # Left side buttons
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side="left", fill="x")
        
        ttk.Button(
            left_buttons,
            text="Add Player",
            command=self.add_player
        ).pack(side="left", padx=5)
        
        # Right side buttons
        right_buttons = ttk.Frame(control_frame)
        right_buttons.pack(side="right", fill="x")
        
        ttk.Button(
            right_buttons,
            text="Update OBS",
            command=self.update_obs_sources_manual
        ).pack(side="right", padx=5)
        
        # Create main players frame
        players_frame = ttk.Frame(self.player_list_frame)
        players_frame.pack(fill="x", expand=True)
        
        # Track player entries
        self.player_entries = []
        
        # Create scrolled frame for players
        self.players_canvas = tk.Canvas(players_frame)
        scrollbar = ttk.Scrollbar(players_frame, orient="vertical", command=self.players_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.players_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.players_canvas.configure(scrollregion=self.players_canvas.bbox("all"))
        )
        
        self.players_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.players_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.players_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create bottom buttons frame
        bottom_frame = ttk.Frame(self.player_list_frame)
        bottom_frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Button(
            bottom_frame,
            text="Copy HTML Links",
            command=lambda: self.copy_all_links(html=True)
        ).pack(side="left", padx=5)
        
        ttk.Button(
            bottom_frame,
            text="Copy Plain Links",
            command=lambda: self.copy_all_links(html=False)
        ).pack(side="left", padx=5)
        
        # Add host entry first
        self.add_host_entry()
        
    def add_host_entry(self):
        """Add the host entry at the top of the player list"""
        # Create frame for host
        host_frame = ttk.Frame(self.scrollable_frame)
        host_frame.pack(fill="x", padx=5, pady=2)
        
        # Host label
        ttk.Label(host_frame, text="Host:", width=8).pack(side="left", padx=2)
        
        # Name entry
        ttk.Label(host_frame, text="Name:", width=6).pack(side="left", padx=2)
        name_entry = ttk.Entry(host_frame, width=20)
        name_entry.pack(side="left", padx=2)
        
        # Character entry
        ttk.Label(host_frame, text="Character:", width=10).pack(side="left", padx=2)
        char_entry = ttk.Entry(host_frame, width=20)
        char_entry.pack(side="left", padx=2)
        
        # Spacer to align with player entries
        ttk.Frame(host_frame).pack(side="left", padx=44)
        
        # Buttons frame
        btn_frame = ttk.Frame(host_frame)
        btn_frame.pack(side="right", padx=2)
        
        # Copy link buttons
        copy_html_btn = ttk.Button(btn_frame, text="Copy HTML",
                                command=lambda: self.copy_host_link(as_html=True))
        copy_html_btn.pack(side="left", padx=2)
        
        copy_text_btn = ttk.Button(btn_frame, text="Copy Link",
                                command=lambda: self.copy_host_link(as_html=False))
        copy_text_btn.pack(side="left", padx=2)
        
        # Store references
        self.host_entry = {
            'frame': host_frame,
            'name': name_entry,
            'character': char_entry
        }
        
        # Bind events
        name_entry.bind('<KeyRelease>', lambda e: self.generate_links())
        char_entry.bind('<KeyRelease>', lambda e: self.generate_links())
        
        # Load host info if available
        if hasattr(self.settings, 'room'):
            name_entry.insert(0, self.settings.room.host_username)
            char_entry.insert(0, self.settings.room.host_character)
    
    def add_player(self):
        """Add a player to the list"""
        # Create frame for this player
        player_frame = ttk.Frame(self.scrollable_frame)
        player_frame.pack(fill="x", padx=5, pady=2)
        
        # Player number
        player_num = len(self.player_entries) + 1
        ttk.Label(player_frame, text=f"Player {player_num}:", width=8).pack(side="left", padx=2)
        
        # Name entry
        ttk.Label(player_frame, text="Name:", width=6).pack(side="left", padx=2)
        name_entry = ttk.Entry(player_frame, width=20)
        name_entry.pack(side="left", padx=2)
        
        # Character entry
        ttk.Label(player_frame, text="Character:", width=10).pack(side="left", padx=2)
        char_entry = ttk.Entry(player_frame, width=20)
        char_entry.pack(side="left", padx=2)
        
        # Buttons frame
        btn_frame = ttk.Frame(player_frame)
        btn_frame.pack(side="right", padx=2)
        
        # Delete button
        delete_btn = ttk.Button(btn_frame, text="Delete",
                              command=lambda f=player_frame, n=name_entry, c=char_entry:
                              self.delete_player_entry(f, n, c))
        delete_btn.pack(side="left", padx=2)
        
        # Store references
        self.player_entries.append({
            'frame': player_frame,
            'name': name_entry,
            'character': char_entry
        })
        
        # Bind events
        name_entry.bind('<KeyRelease>', lambda e: self.generate_links())
        char_entry.bind('<KeyRelease>', lambda e: self.generate_links())
        
        # Update links
        self.generate_links()

    def delete_player_entry(self, frame, name_entry, char_entry):
        """Delete a player entry"""
        # Remove from player entries
        self.player_entries = [p for p in self.player_entries 
                             if p['frame'] != frame]
        
        # Destroy the frame
        frame.destroy()
        
        # Renumber remaining players
        for i, entry in enumerate(self.player_entries, 1):
            label = entry['frame'].winfo_children()[0]
            label.configure(text=f"Player {i}:")
        
        # Update links
        self.generate_links()

    def generate_links(self):
        """Generate all links"""
        try:
            links = {}
            
            # Get room name and password
            room_name = self.room_config.get_room_name()
            if not room_name:
                raise ValueError("Room name is not set")
            
            password = self.room_config.get_room_password()
            
            # Update settings with current values
            self.settings.room.room_name = room_name
            self.settings.room.room_password = self.room_config.get_room_password()
            
            # Save host info
            if hasattr(self, 'host_entry'):
                self.settings.room.host_username = self.host_entry['name'].get().strip()
                self.settings.room.host_character = self.host_entry['character'].get().strip()
            
            # Generate host/director params
            params = {
                "room": room_name,
                "director": "1",
                "quality": "1080p",
                "meshcast": "1"
            }
            
            # Only add password if it exists
            if password:
                params["password"] = password
            
            # Add host name if provided
            if self.settings.room.host_username:
                params["username"] = self.settings.room.host_username
            
            # Add host character if provided
            if self.settings.room.host_character:
                params["character"] = self.settings.room.host_character
            
            links['host'] = "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in params.items())
            
            # Generate player links
            for entry in self.player_entries:
                username = entry['name'].get().strip()
                character = entry['character'].get().strip()
                
                if username:  # Only generate link if username is provided
                    player_params = {
                        "room": room_name,
                        "username": username,
                        "quality": "1080p",
                        "meshcast": "1"
                    }
                    
                    # Only add password if it exists
                    if password:
                        player_params["password"] = password
                    
                    # Add character if provided
                    if character:
                        player_params["character"] = character
                    
                    player_url = "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in player_params.items())
                    links[username] = player_url
            
            # Update OBS sources if connected
            self.update_obs_sources(links)
            
            return links
            
        except Exception as e:
            self.logger.error(f"Failed to generate links: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate links: {str(e)}")

    def create_debug_frame(self):
        """Create the debug frame"""
        # Create frame
        debug_frame = ttk.LabelFrame(self.main_frame, text="Debug Log")
        debug_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create text widget with scrollbar
        self.debug_text = tk.Text(debug_frame, height=8)
        scrollbar = ttk.Scrollbar(debug_frame, orient="vertical", command=self.debug_text.yview)
        self.debug_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.debug_text.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0,5), pady=5)
        
        # Create button frame
        button_frame = ttk.Frame(debug_frame)
        button_frame.pack(fill="x", padx=5, pady=(0,5))
        
        # Add buttons
        ttk.Button(
            button_frame,
            text="Copy Debug Info",
            command=self.copy_debug_info
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_debug_log
        ).pack(side="left", padx=5)

    def show_documentation(self):
        """Show documentation in web browser"""
        try:
            doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documentation.html")
            webbrowser.open(doc_path)
        except Exception as e:
            self.logger.error(f"Failed to open documentation: {str(e)}")
            messagebox.showerror("Error", f"Failed to open documentation: {str(e)}")

    def show_settings(self):
        """Show the settings dialog"""
        dialog = SettingsDialog(self.root, self.settings)
        dialog.transient(self.root)
        dialog.grab_set()
        
        def on_save():
            self.settings.save()
            self.connect_to_obs()
            dialog.destroy()
        
        dialog.on_save = on_save
        
    def save_room(self):
        """Save current room configuration"""
        try:
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Room Configuration"
            )
            
            if not file_path:
                return
            
            # Update settings with current values
            self.settings.room.room_name = self.room_config.get_room_name()
            self.settings.room.room_password = self.room_config.get_room_password()
            
            # Save host info
            if hasattr(self, 'host_entry'):
                self.settings.room.host_username = self.host_entry['name'].get().strip()
                self.settings.room.host_character = self.host_entry['character'].get().strip()
            
            self.settings.room.players.clear()
            
            # Add player data to settings
            for entry in self.player_entries:
                name = entry['name'].get().strip()
                character = entry['character'].get().strip()
                if name:  # Only add if name is provided
                    self.settings.room.players[name] = character
            
            # Save using settings class method
            self.settings.save_room(file_path)
            messagebox.showinfo("Success", "Room configuration saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to save room: {str(e)}")
            messagebox.showerror("Error", f"Failed to save room configuration: {str(e)}")

    def load_room_dialog(self):
        """Show dialog to load room configuration"""
        try:
            # Get file path
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Room Configuration"
            )
            
            if not file_path:
                return
                
            # Load from file
            with open(file_path, 'r') as f:
                room_data = json.load(f)
            
            # Update settings first
            self.settings.room.from_dict(room_data)
            
            # Update UI with loaded settings
            self.room_config.set_room_name(self.settings.room.room_name)
            self.room_config.set_room_password(self.settings.room.room_password)
            
            # Update host fields
            self.host_entry['name'].delete(0, tk.END)
            self.host_entry['name'].insert(0, self.settings.room.host_username)
            self.host_entry['character'].delete(0, tk.END)
            self.host_entry['character'].insert(0, self.settings.room.host_character)
            
            # Clear existing players
            for entry in self.player_entries:
                entry['frame'].destroy()
            self.player_entries.clear()
            
            # Add loaded players from settings
            for name, character in self.settings.room.players.items():
                # Create new player entry
                player_frame = ttk.Frame(self.scrollable_frame)
                player_frame.pack(fill="x", padx=5, pady=2)
                
                # Player number
                player_num = len(self.player_entries) + 1
                ttk.Label(player_frame, text=f"Player {player_num}:", width=8).pack(side="left", padx=2)
                
                # Name entry
                ttk.Label(player_frame, text="Name:", width=6).pack(side="left", padx=2)
                name_entry = ttk.Entry(player_frame, width=20)
                name_entry.insert(0, name)
                name_entry.pack(side="left", padx=2)
                
                # Character entry
                ttk.Label(player_frame, text="Character:", width=10).pack(side="left", padx=2)
                char_entry = ttk.Entry(player_frame, width=20)
                char_entry.insert(0, character)
                char_entry.pack(side="left", padx=2)
                
                # Buttons frame
                btn_frame = ttk.Frame(player_frame)
                btn_frame.pack(side="right", padx=2)
                
                # Delete button
                delete_btn = ttk.Button(btn_frame, text="Delete",
                                      command=lambda f=player_frame, n=name_entry, c=char_entry:
                                      self.delete_player_entry(f, n, c))
                delete_btn.pack(side="left", padx=2)
                
                # Store references
                self.player_entries.append({
                    'frame': player_frame,
                    'name': name_entry,
                    'character': char_entry
                })
                
                # Bind events
                name_entry.bind('<KeyRelease>', lambda e: self.generate_links())
                char_entry.bind('<KeyRelease>', lambda e: self.generate_links())
            
            # Generate links for loaded configuration
            self.generate_links()
            messagebox.showinfo("Success", "Room configuration loaded successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to load room: {str(e)}")
            messagebox.showerror("Error", f"Failed to load room configuration: {str(e)}")

    def connect_to_obs(self):
        """Try to connect to OBS"""
        if self.settings.interface.enable_obs:
            try:
                self.obs_manager.connect(
                    host=self.settings.obs.host,
                    port=self.settings.obs.port,
                    password=self.settings.obs.password
                )
                self.logger.info("Successfully connected to OBS")
            except Exception as e:
                self.logger.error(f"Failed to connect to OBS: {str(e)}")
        else:
            self.logger.info("OBS integration is disabled")
            
    def update_obs_sources(self, links=None):
        """Update OBS sources with the current links"""
        try:
            self.logger.info("Starting to update OBS sources...")
            if not hasattr(self, 'obs_manager') or self.obs_manager is None:
                self.logger.info("OBS manager not initialized, skipping source update")
                return
            
            if links is None:
                links = self.generate_links()
            
            self.obs_manager.update_sources(links)
            self.logger.info("Successfully updated OBS sources")
            
        except Exception as e:
            self.logger.error(f"Failed to update OBS sources: {str(e)}")
            if hasattr(traceback, 'format_exc'):
                self.logger.error(traceback.format_exc())
    
    def update_obs_sources_manual(self):
        """Manually update OBS sources and host label"""
        try:
            # Generate links first
            self.generate_links()
            
            if self.obs_manager and self.obs_manager.is_connected():
                # Get host name
                host_name = ""
                if hasattr(self, 'host_entry'):
                    host_name = self.host_entry['name'].get().strip()
                
                # Update host label in OBS
                if host_name:
                    self.obs_manager.update_text_source("p0name", host_name)
                
                messagebox.showinfo("Success", "OBS sources and labels updated!")
            else:
                messagebox.showwarning("Warning", "OBS is not connected. Please check connection settings.")
        except Exception as e:
            self.logger.error(f"Failed to update OBS sources: {str(e)}")
            messagebox.showerror("Error", f"Failed to update OBS sources: {str(e)}")

    def copy_all_links(self, html=False):
        """Copy all links to clipboard"""
        try:
            links = self.generate_links()
            
            if html:
                html_links = "\n".join(f'<a href="{url}">{name}</a>' for name, url in links.items())
                self.root.clipboard_clear()
                self.root.clipboard_append(html_links)
                self.root.update()
                messagebox.showinfo("Success", "All links copied to clipboard as HTML!")
            else:
                plain_links = "\n".join(f"{name}: {url}" for name, url in links.items())
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_links)
                self.root.update()
                messagebox.showinfo("Success", "All links copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy links: {str(e)}")

    def copy_player_link(self, username: str, character: str, as_html=False):
        """Copy a player's link to clipboard"""
        try:
            # Get room name
            room_name = self.room_config.get_room_name()
            if not room_name:
                raise ValueError("Room name is not set")
            
            # Build URL parameters
            params = {
                "room": room_name,
                "username": username,
                "quality": "1080p",
                "meshcast": "1"
            }
            
            # Only add password if it exists
            password = self.room_config.get_room_password()
            if password:
                params["password"] = password
            
            # Add character if provided
            if character:
                params["character"] = character
            
            # Generate URL
            url = "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in params.items())
            
            # Copy to clipboard
            if as_html:
                html = f'<a href="{url}">Link for {username}</a>'
                self.root.clipboard_clear()
                self.root.clipboard_append(html)
                self.root.update()
                messagebox.showinfo("Success", f"Link for {username} copied to clipboard as HTML!")
            else:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.root.update()
                messagebox.showinfo("Success", f"Link for {username} copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy link: {str(e)}")

    def copy_host_link(self, as_html=False):
        """Copy the host link to clipboard"""
        try:
            # Get room name
            room_name = self.room_config.get_room_name()
            if not room_name:
                raise ValueError("Room name is not set")
            
            # Build URL parameters
            params = {
                "room": room_name,
                "director": "1",
                "quality": "1080p",
                "meshcast": "1"
            }
            
            # Only add password if it exists
            password = self.room_config.get_room_password()
            if password:
                params["password"] = password
            
            # Add host name if provided
            if hasattr(self, 'host_entry'):
                host_name = self.host_entry['name'].get().strip()
                if host_name:
                    params["username"] = host_name
            
            # Add host character if provided
            if hasattr(self, 'host_entry'):
                host_char = self.host_entry['character'].get().strip()
                if host_char:
                    params["character"] = host_char
            
            # Generate URL
            url = "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in params.items())
            
            # Copy to clipboard
            if as_html:
                html = f'<a href="{url}">Host Link</a>'
                self.root.clipboard_clear()
                self.root.clipboard_append(html)
                self.root.update()
                messagebox.showinfo("Success", "Host link copied to clipboard as HTML!")
            else:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.root.update()
                messagebox.showinfo("Success", "Host link copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy host link: {str(e)}")

    def log_debug(self, message: str):
        """Write a debug message to the log"""
        self.logger.info(message)
        self.update_debug_info()

    def get_debug_info(self):
        """Get debug info"""
        # Check actual OBS connection state
        obs_connected = False
        if hasattr(self, 'obs_manager') and self.obs_manager is not None:
            try:
                obs_connected = self.obs_manager.is_connected()
            except Exception as e:
                self.logger.error(f"Error checking OBS connection: {str(e)}")
        
        # Build header info
        header_info = [
            "=== VDO.Ninja Link Manager Debug Info ===",
            f"OBS Connected: {obs_connected}",
            f"OBS Host: {self.settings.obs.host}",
            f"OBS Port: {self.settings.obs.port}",
            "=== Debug Log ===",
        ]
        
        # Get log content
        try:
            with open(self.debug_log_path, 'r') as f:
                log_content = f.read()
        except Exception as e:
            log_content = f"Error reading debug log: {str(e)}"
        
        return "\n".join(header_info + [log_content])

    def update_debug_info(self):
        """Update debug info display"""
        if hasattr(self, 'debug_text'):
            self.debug_text.delete('1.0', tk.END)
            self.debug_text.insert(tk.END, self.get_debug_info())
            
    def copy_debug_info(self):
        """Copy debug info to clipboard"""
        debug_info = self.get_debug_info()
        self.root.clipboard_clear()
        self.root.clipboard_append(debug_info)
        self.root.update()
        messagebox.showinfo("Success", "Debug info copied to clipboard!")
    
    def clear_debug_log(self):
        """Clear the debug log"""
        try:
            with open(self.debug_log_path, 'w') as f:
                f.write("")
            self.logger.info("Debug log cleared")
            self.update_debug_info()
            messagebox.showinfo("Success", "Debug log cleared!")
        except Exception as e:
            self.logger.error(f"Failed to clear debug log: {str(e)}")
            messagebox.showerror("Error", f"Failed to clear debug log: {str(e)}")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()
