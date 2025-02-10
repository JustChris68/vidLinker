import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import re

from settings import Settings
from obs_manager import OBSManager
from vdo_ninja_manager import VDONinjaManager
from ui_components import SettingsDialog, ScrollableFrame

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
        self.on_change_callback = None
    
    def get_player_info(self):
        return {
            "name": self.name_var.get(),
            "character": self.char_var.get()
        }
    
    def set_delete_callback(self, callback):
        self.on_delete_callback = callback
    
    def set_change_callback(self, callback):
        self.on_change_callback = callback
    
    def on_delete(self):
        if self.on_delete_callback:
            self.on_delete_callback(self)
    
    def on_change(self):
        if self.on_change_callback:
            self.on_change_callback()

class RoomConfigFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Room name frame
        room_frame = ttk.Frame(self)
        room_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(room_frame, text="Room Name:").pack(side="left", padx=(0,5))
        self.room_var = tk.StringVar()
        ttk.Entry(room_frame, textvariable=self.room_var).pack(side="left", fill="x", expand=True)
        
        # Password frame
        pass_frame = ttk.Frame(self)
        pass_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(pass_frame, text="Password:").pack(side="left", padx=(0,5))
        self.pass_var = tk.StringVar()
        ttk.Entry(pass_frame, textvariable=self.pass_var).pack(side="left", fill="x", expand=True)
        
        # Host frame
        host_frame = ttk.LabelFrame(self, text="Host Settings")
        host_frame.pack(fill="x", padx=5, pady=5)
        
        # Host name
        host_name_frame = ttk.Frame(host_frame)
        host_name_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(host_name_frame, text="Host Name:").pack(side="left", padx=(0,5))
        self.host_name_var = tk.StringVar()
        ttk.Entry(host_name_frame, textvariable=self.host_name_var).pack(side="left", fill="x", expand=True)
        
        # Host character
        host_char_frame = ttk.Frame(host_frame)
        host_char_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(host_char_frame, text="Host Character:").pack(side="left", padx=(0,5))
        self.host_char_var = tk.StringVar()
        ttk.Entry(host_char_frame, textvariable=self.host_char_var).pack(side="left", fill="x", expand=True)
        
        # Players frame
        players_label_frame = ttk.Frame(self)
        players_label_frame.pack(fill="x", padx=5, pady=(10,0))
        ttk.Label(players_label_frame, text="Players:").pack(side="left")
        ttk.Button(players_label_frame, text="Add Player", command=self.add_player).pack(side="right")
        
        # Scrollable frame for players
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.winfo_width())
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # List to keep track of player frames
        self.player_frames = []
        
        # Add initial player
        self.add_player()
        
        # Bind resize event
        self.bind("<Configure>", self.on_resize)
        
        # Bind variable trace for auto-update
        self.room_var.trace_add("write", self.on_config_change)
        self.pass_var.trace_add("write", self.on_config_change)
        self.host_name_var.trace_add("write", self.on_config_change)
        self.host_char_var.trace_add("write", self.on_config_change)
    
    def on_config_change(self, *args):
        """Called when any configuration value changes"""
        # Get the root window
        root = self.winfo_toplevel()
        if hasattr(root, "generate_links"):
            root.generate_links()
    
    def on_resize(self, event):
        # Update canvas window width when frame is resized
        if event.widget == self:
            self.canvas.itemconfig(1, width=event.width-30)  # Subtract scrollbar width and padding
    
    def add_player(self):
        player_num = len(self.player_frames) + 1
        player_frame = PlayerFrame(self.scrollable_frame, player_num)
        player_frame.pack(fill="x", padx=5, pady=2)
        player_frame.set_delete_callback(self.remove_player)
        player_frame.set_change_callback(self.on_config_change)
        self.player_frames.append(player_frame)
        
        # Update player numbers
        self.renumber_players()
    
    def remove_player(self, player_frame):
        if len(self.player_frames) > 1:  # Keep at least one player
            player_frame.pack_forget()
            player_frame.destroy()
            self.player_frames.remove(player_frame)
            # Update player numbers
            self.renumber_players()
    
    def renumber_players(self):
        for i, frame in enumerate(self.player_frames, 1):
            frame.player_num = i
            # Update the label in the first child frame (info_frame)
            for child in frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for label in child.winfo_children():
                        if isinstance(label, ttk.Label) and label.cget("text").startswith("Player"):
                            label.configure(text=f"Player {i}:")
                            break
                    break
    
    def get_config(self):
        config = {
            "room": self.room_var.get(),
            "password": self.pass_var.get(),
            "host_username": self.host_name_var.get(),
            "host_character": self.host_char_var.get(),
            "players": {}
        }
        
        for frame in self.player_frames:
            player_info = frame.get_player_info()
            if player_info["name"]:  # Only include players with names
                config["players"][player_info["name"]] = player_info["character"]
        
        return config
    
    def set_config(self, config):
        self.room_var.set(config.get("room", ""))
        self.pass_var.set(config.get("password", ""))
        self.host_name_var.set(config.get("host_username", ""))
        self.host_char_var.set(config.get("host_character", ""))
        
        # Clear existing players
        for frame in self.player_frames:
            frame.pack_forget()
            frame.destroy()
        self.player_frames.clear()
        
        # Add players from config
        players = config.get("players", {})
        if not players:
            self.add_player()  # Add one empty player if none in config
        else:
            for name, character in players.items():
                player_frame = PlayerFrame(self.scrollable_frame, len(self.player_frames) + 1, name, character)
                player_frame.pack(fill="x", padx=5, pady=2)
                player_frame.set_delete_callback(self.remove_player)
                player_frame.set_change_callback(self.on_config_change)
                self.player_frames.append(player_frame)

class App:
    def __init__(self):
        """Initialize the application"""
        self.settings = Settings()
        self.settings.load()
        
        self.root = tk.Tk()
        self.root.title("VDO.Ninja Link Manager")
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Room configuration frame
        self.room_config = RoomConfigFrame(self.main_frame)
        self.room_config.pack(fill="both", expand=True)
        
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill="x", pady=10)
        
        # Buttons
        ttk.Button(
            button_frame,
            text="Save Room",
            command=self.save_room
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Load Room",
            command=self.load_room_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Settings",
            command=self.show_settings
        ).pack(side="left", padx=5)
        
        if self.settings.interface.enable_obs:
            self.obs_button = ttk.Button(button_frame, text="Update OBS", command=self.update_obs_sources)
            self.obs_button.pack(side="left", padx=5)
        
        # Documentation button
        ttk.Button(
            button_frame,
            text="Documentation",
            command=self.show_documentation
        ).pack(side="left", padx=5)
        
        # Links frame
        self.links_frame = ttk.LabelFrame(self.main_frame, text="Generated Links")
        self.links_frame.pack(fill="both", expand=True, pady=10)
        
        # Debug frame
        self.debug_frame = ttk.LabelFrame(self.main_frame, text="Debug Info")
        self.debug_frame.pack(fill="both", expand=True, pady=10)
        
        # Debug buttons
        buttons_frame = ttk.Frame(self.debug_frame)
        buttons_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(buttons_frame, text="Copy Debug Info", command=self.copy_debug_info).pack(side="left", padx=2)
        ttk.Button(buttons_frame, text="Clear Debug Log", command=self.clear_debug_log).pack(side="left", padx=2)
        
        # Debug text
        self.debug_text = tk.Text(self.debug_frame, height=10)
        self.debug_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initial debug info
        self.update_debug_info()
        
        # Initialize managers
        self.obs_manager = OBSManager()
        self.vdo_manager = VDONinjaManager()
        
        # Try to connect to OBS
        self.connect_to_obs()
        
        # Load initial room config if exists
        if self.settings.room and self.settings.room.room_name:
            self.room_config.set_config({
                "room": self.settings.room.room_name,
                "password": self.settings.room.room_password,
                "players": self.settings.room.players
            })
            self.generate_links()
            
    def show_documentation(self):
        """Show documentation in a new window"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("VDO.Ninja Link Manager Documentation")
        doc_window.geometry("600x400")
        
        doc_text = tk.Text(doc_window, wrap="word", padx=10, pady=10)
        doc_text.pack(fill="both", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(doc_window, orient="vertical", command=doc_text.yview)
        scrollbar.pack(side="right", fill="y")
        doc_text.configure(yscrollcommand=scrollbar.set)
        
        documentation = """
VDO.Ninja Link Manager Documentation

Overview:
---------
The VDO.Ninja Link Manager helps you create and manage permanent links for VDO.Ninja rooms.
It integrates with OBS to automatically update sources when links change.

Features:
---------
1. Room Management
   - Create and save room configurations
   - Set room name and password
   - Add/remove players
   - Set player names and character names

2. Link Generation
   - Generates host/director link with OBS control
   - Generates individual player links
   - All links use meshcast for improved performance
   - Default 1080p resolution

3. OBS Integration
   - Automatically creates/updates browser sources
   - Organizes sources in a dedicated "VDO Assets" scene
   - Updates names based on player/character names

Usage:
------
1. Room Configuration
   - Enter room name and password
   - Add players using the "Add Player" button
   - Set player names and character names
   - Delete players using the "Delete" button

2. Managing Links
   - Links are automatically generated when you save
   - Use "Copy" buttons to copy links to clipboard
   - Links include all necessary parameters

3. OBS Integration
   - Enable OBS in settings
   - Set host, port, and password
   - Use "Update OBS" to refresh sources

Tips:
-----
- Always save your room configuration
- Test links before sharing with players
- Check debug log for troubleshooting
"""
        
        doc_text.insert("1.0", documentation)
        doc_text.configure(state="disabled")
        
    def copy_debug_info(self):
        """Copy debug info to clipboard"""
        debug_info = self.get_debug_info()
        self.root.clipboard_clear()
        self.root.clipboard_append(debug_info)
        messagebox.showinfo("Success", "Debug info copied to clipboard!")
    
    def clear_debug_log(self):
        """Clear the debug log"""
        try:
            with open(self.debug_log_path, 'w') as f:
                f.write("")
            self.log_debug("Debug log cleared")
            self.update_debug_info()
            messagebox.showinfo("Success", "Debug log cleared!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear debug log: {str(e)}")
    
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
        """Save the current room configuration"""
        config = self.room_config.get_config()
        if not config["room"].strip():
            messagebox.showerror("Error", "Room name is required")
            return
            
        # Update settings with current UI values
        self.settings.room.room_name = config["room"]
        self.settings.room.room_password = config["password"]
        self.settings.room.players = config["players"]
        
        # Update player_info for backward compatibility
        self.settings.room.player_info = "\n".join(f"{name},{char}" for name, char in config["players"].items())
        
        # Let user choose where to save
        filename = filedialog.asksaveasfilename(
            title="Save Room Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            initialfile=f"{self.settings.room.room_name}_room.json"
        )
        
        if filename:
            try:
                self.settings.save_room(filename)
                self.generate_links()
                self.log_debug(f"Successfully saved room: {self.settings.room.room_name}")
                messagebox.showinfo("Success", "Room configuration saved successfully")
            except Exception as e:
                self.log_debug(f"Failed to save room: {str(e)}")
                messagebox.showerror("Error", f"Failed to save room: {str(e)}")
                
    def load_room_dialog(self):
        """Show dialog to load a room configuration"""
        filename = filedialog.askopenfilename(
            title="Load Room Configuration",
            filetypes=[("JSON files", "*.json")],
            initialdir=os.path.dirname(os.path.abspath(__file__))
        )
        if filename:
            try:
                self.settings.load_room(filename)
                
                # Set the room configuration in the UI
                config = {
                    "room": self.settings.room.room_name,
                    "password": self.settings.room.room_password,
                    "players": {}
                }
                
                # Handle both old and new formats
                if self.settings.room.player_info:
                    for line in self.settings.room.player_info.splitlines():
                        if line.strip():
                            try:
                                username, character = map(str.strip, line.split(','))
                                config["players"][username] = character
                            except ValueError:
                                continue
                else:
                    config["players"] = self.settings.room.players
                
                self.room_config.set_config(config)
                self.generate_links()
                self.log_debug(f"Successfully loaded room: {self.settings.room.room_name}")
                messagebox.showinfo("Success", "Room configuration loaded successfully")
            except Exception as e:
                self.log_debug(f"Failed to load room: {str(e)}")
                messagebox.showerror("Error", f"Failed to load room: {str(e)}")
                
    def generate_links(self):
        """Generate VDO.Ninja links based on current configuration"""
        try:
            if not self.settings.room.room_name:
                raise ValueError("Room name is not set")
                
            # Clear existing links
            for widget in self.links_frame.winfo_children():
                widget.destroy()
                
            # Create links frame
            self.links_list = ttk.Treeview(self.links_frame, columns=("Link",), show="tree")
            self.links_list.pack(fill="both", expand=True, padx=5, pady=5)
            self.links_list.column("#0", width=150)
            self.links_list.column("Link", width=400)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(self.links_frame, orient="vertical", command=self.links_list.yview)
            scrollbar.pack(side="right", fill="y")
            self.links_list.configure(yscrollcommand=scrollbar.set)
            
            # Add buttons frame
            buttons_frame = ttk.Frame(self.links_frame)
            buttons_frame.pack(fill="x", padx=5, pady=5)
            
            # Copy buttons
            ttk.Button(buttons_frame, text="Copy HTML Links", command=self.copy_html_links).pack(side="left", padx=2)
            ttk.Button(buttons_frame, text="Copy Plain Links", command=self.copy_plain_links).pack(side="left", padx=2)
            ttk.Button(buttons_frame, text="Update OBS", command=self.update_obs_sources).pack(side="right", padx=2)
            
            # Host link
            host_link = self.settings.room.get_host_link()
            self.links_list.insert("", "end", text="Host Link", values=(host_link,))
            
            # Player links
            for player_name in self.settings.room.players:
                player_link = self.settings.room.get_player_link(player_name)
                self.links_list.insert("", "end", text=f"{player_name} Link", values=(player_link,))
                
            # Update OBS sources
            self.update_obs_sources()
            
        except Exception as e:
            self.log_debug(f"Cannot generate links: {str(e)}")
            
    def connect_to_obs(self):
        """Try to connect to OBS"""
        if self.settings.interface.enable_obs:
            try:
                self.obs_manager.connect(
                    host=self.settings.obs.host,
                    port=self.settings.obs.port,
                    password=self.settings.obs.password
                )
                self.log_debug("Successfully connected to OBS")
            except Exception as e:
                self.log_debug(f"Failed to connect to OBS: {str(e)}")
        else:
            self.log_debug("OBS integration is disabled")
            
    def update_obs_sources(self):
        """Update OBS sources with current links"""
        try:
            links = {}
            self.log_debug("Starting to collect links...")
            
            # Get host/director link first
            host_link = self.settings.room.get_host_link()
            if host_link:
                links["director"] = host_link
                self.log_debug("Added host/director link")
            else:
                self.log_debug("Warning: No host link found")
            
            # Get player links
            for username in self.settings.room.players:
                try:
                    player_link = self.settings.room.get_player_link(username)
                    if player_link:
                        links[username] = player_link
                        self.log_debug(f"Added link for player: {username}")
                    else:
                        self.log_debug(f"Warning: No link generated for player {username}")
                except Exception as e:
                    self.log_debug(f"Error generating link for player {username}: {str(e)}")
            
            if links:
                self.log_debug(f"Found links for: {', '.join(links.keys())}")
                try:
                    self.obs_manager.update_sources(links)
                    self.log_debug("Successfully updated OBS sources")
                except Exception as e:
                    error_msg = f"Failed to update OBS sources: {str(e)}"
                    self.log_debug(error_msg)
                    if hasattr(e, '__traceback__'):
                        import traceback
                        self.log_debug("Traceback:")
                        self.log_debug(traceback.format_exc())
                    messagebox.showerror("Error", error_msg)
            else:
                error_msg = "No links found to update OBS sources"
                self.log_debug(error_msg)
                messagebox.showerror("Error", error_msg)
                
        except Exception as e:
            error_msg = f"Failed to update OBS sources: {str(e)}"
            self.log_debug(error_msg)
            if hasattr(e, '__traceback__'):
                import traceback
                self.log_debug("Traceback:")
                self.log_debug(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
    
    def copy_html_links(self):
        """Copy links in HTML format"""
        html_links = ["<h2>VDO.Ninja Links</h2>", "<ul>"]
        for item_id in self.links_list.get_children():
            desc = self.links_list.item(item_id)["text"]
            link = self.links_list.item(item_id)["values"][0]
            html_links.append(f'<li><strong>{desc}:</strong> <a href="{link}">{link}</a></li>')
        html_links.append("</ul>")
        
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(html_links))
        messagebox.showinfo("Success", "HTML links copied to clipboard!")
    
    def copy_plain_links(self):
        """Copy links in plain text format"""
        plain_links = ["VDO.Ninja Links:"]
        for item_id in self.links_list.get_children():
            desc = self.links_list.item(item_id)["text"]
            link = self.links_list.item(item_id)["values"][0]
            plain_links.append(f"{desc}: {link}")
        
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(plain_links))
        messagebox.showinfo("Success", "Plain text links copied to clipboard!")
    
    def log_debug(self, message):
        """Log debug message with timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"{timestamp}: {message}"
            
            # Update debug text
            if hasattr(self, 'debug_text'):
                self.debug_text.insert("1.0", log_message + "\n")
            
            # Write to log file
            with open(self.debug_log_path, 'a') as f:
                f.write(log_message + "\n")
        except Exception as e:
            print(f"Error writing debug log: {str(e)}")
    
    def get_debug_info(self):
        """Get debug info"""
        # Check actual OBS connection state
        obs_connected = False
        if hasattr(self, 'obs_manager'):
            try:
                obs_connected = self.obs_manager.is_connected()
            except Exception as e:
                self.log_debug(f"Error checking OBS connection: {str(e)}")
        
        debug_info = [
            "=== VDO.Ninja Link Manager Debug Info ===",
            f"OBS Connected: {obs_connected}",
            f"OBS Host: {self.settings.obs.host}",
            f"OBS Port: {self.settings.obs.port}",
            "=== Debug Log ===",
            self.debug_text.get("1.0", tk.END) if hasattr(self, 'debug_text') else ""
        ]
        
        return "\n".join(debug_info)
    
    def update_debug_info(self):
        """Update debug info display"""
        if hasattr(self, 'debug_text'):
            self.debug_text.delete("1.0", tk.END)
            self.debug_text.insert("1.0", self.get_debug_info())
            
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()
