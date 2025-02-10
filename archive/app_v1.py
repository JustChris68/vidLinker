import sys
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import webbrowser
from pathlib import Path
import hashlib
import base64
import logging
from obswebsocket import obsws, requests
from urllib.parse import urlparse, parse_qs, urlencode
import requests
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('VDONinja')
handler = logging.FileHandler('obs_debug.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class LinkButton(ttk.Frame):
    """A custom widget that combines a label with a copy button"""
    def __init__(self, parent, url, text, use_tinyurl=True, *args, **kwargs):
        # Remove use_tinyurl from kwargs before passing to parent
        if 'use_tinyurl' in kwargs:
            del kwargs['use_tinyurl']
        super().__init__(parent, *args, **kwargs)
        
        self.url = url
        # Only shorten URL if use_tinyurl is True
        self.display_url = self.shorten_url(url) if use_tinyurl else url
        
        # Create and pack the label
        self.label = ttk.Label(self, text=f"{text}: {self.display_url}")
        self.label.pack(side="left", padx=5)
        
        # Create and pack the copy button
        self.copy_btn = ttk.Button(self, text="Copy", command=self.copy_to_clipboard)
        self.copy_btn.pack(side="right", padx=5)

    def shorten_url(self, url):
        """Shorten URL using TinyURL service"""
        try:
            return requests.get(f"https://tinyurl.com/api-create.php?url={url}").text
        except:
            return url
            
    def copy_to_clipboard(self):
        """Copy the URL to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.url)

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class CreateToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        
    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()
        
    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class VDONinjaManager:
    def __init__(self, root):
        self.root = root
        self.root.title("VDO.Ninja Link Manager")
        self.root.geometry("600x800")
        
        # Store player info for OBS updates and HTML generation
        self.player_sources = []
        self.player_links = []
        self.current_room_name = None
        
        # Menu Bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Room", command=self.save_room)
        file_menu.add_command(label="Save Room As...", command=self.save_room_as)
        file_menu.add_command(label="Load Room", command=self.load_room)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        
        # Configuration section
        config_frame = ttk.LabelFrame(root, text="Configuration", padding="5")
        config_frame.pack(fill="x", padx=5, pady=5)
        
        # Room Name
        room_name_frame = ttk.Frame(config_frame)
        room_name_frame.pack(fill="x", pady=2)
        ttk.Label(room_name_frame, text="Room Name:").pack(side="left")
        self.room_name = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.room_name).pack(side="left", padx=5, fill="x", expand=True)
        
        # Host configuration section
        host_frame = ttk.LabelFrame(config_frame, text="Host Configuration", padding="5")
        host_frame.pack(fill="x", pady=5)
        
        # Host username
        host_name_frame = ttk.Frame(host_frame)
        host_name_frame.pack(fill="x", pady=2)
        ttk.Label(host_name_frame, text="Host Username:").pack(side="left")
        self.host_username = ttk.Entry(host_name_frame)
        self.host_username.pack(side="left", padx=5)
        
        # Host character name
        host_char_frame = ttk.Frame(host_frame)
        host_char_frame.pack(fill="x", pady=2)
        ttk.Label(host_char_frame, text="Host Character:").pack(side="left")
        self.host_character = ttk.Entry(host_char_frame)
        self.host_character.pack(side="left", padx=5)
        
        # Room password
        password_frame = ttk.LabelFrame(host_frame, text="Room Password", padding="5")
        password_frame.pack(fill="x", pady=2)
        
        # Password entry
        password_entry_frame = ttk.Frame(password_frame)
        password_entry_frame.pack(fill="x", pady=2)
        ttk.Label(password_entry_frame, text="Password:").pack(side="left")
        self.room_password = ttk.Entry(password_entry_frame)
        self.room_password.pack(side="left", padx=5)
        
        # Password inclusion options
        password_options_frame = ttk.Frame(password_frame)
        password_options_frame.pack(fill="x", pady=2)
        self.password_inclusion = tk.StringVar(value="include")
        ttk.Radiobutton(password_options_frame, 
                       text="Include password in links", 
                       variable=self.password_inclusion,
                       value="include").pack(side="left", padx=5)
        ttk.Radiobutton(password_options_frame, 
                       text="Exclude password from links", 
                       variable=self.password_inclusion,
                       value="exclude").pack(side="left", padx=5)
        
        # Player configuration
        ttk.Label(config_frame, text="Player Information (one per line):").pack(anchor="w", padx=5)
        ttk.Label(config_frame, text="Format: username,character_name").pack(anchor="w", padx=5)
        self.player_info = scrolledtext.ScrolledText(config_frame, height=5)
        self.player_info.pack(fill="x", padx=5, pady=5)
        
        # Generate button
        self.generate_btn = ttk.Button(config_frame, text="Generate Links", command=self.generate_link)
        self.generate_btn.pack(pady=5)
        
        # URL Options button
        self.url_options_btn = ttk.Button(config_frame, text="URL Options", command=self.show_url_options)
        self.url_options_btn.pack(pady=5)
        
        # Links section
        self.links_frame = ScrollableFrame(root)
        self.links_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load saved configurations
        self.config_file = Path("room_config.json")
        self.load_config()

    def generate_permanent_id(self, seed):
        """Generate a permanent push ID based on username and character"""
        return hashlib.md5(seed.encode()).hexdigest()[:12]

    def shorten_url(self, url):
        """Shorten a URL using TinyURL's API"""
        try:
            response = requests.get(f'http://tinyurl.com/api-create.php?url={url}')
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to shorten URL: {response.status_code}")
                return url
        except Exception as e:
            logger.error(f"Error shortening URL: {str(e)}")
            return url

    def generate_link(self):
        # Clear previous links
        for widget in self.links_frame.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Reset sources list
        self.player_sources = []
        self.player_links = []
        
        # Get user inputs
        host = self.host_username.get().strip()
        password = self.room_password.get().strip()
        include_password = self.password_inclusion.get() == "include"
        
        if not host or not password:
            messagebox.showerror("Error", "Host username and room password are required")
            return
        
        # Generate room name - always use the same format for consistency
        room_name = f"vidlinker_{host}_{password}"
        
        # Base URL and common parameters
        base_url = "https://vdo.ninja/?"
        common_params = {
            "room": room_name,
            "meshcast": "1",
            "quality": "1080"
        }
        
        # Host always gets the password in their link
        host_params = {
            "room": room_name,
            "password": password,  # Host always needs password
            "director": None,  # Using None to ensure it appears as &director
            "name": host,
            "label": f"{host}/{self.host_character.get().strip()}"
        }
        
        # Special URL handling to ensure &director appears without value
        host_link = base_url + "&".join(k if v is None else f"{k}={v}" for k, v in host_params.items())
        
        # Create button for host link
        LinkButton(self.links_frame.scrollable_frame, 
                  host_link, 
                  f"Host Link: {host}").pack(fill="x")
        
        # Add interface options if enabled
        if hasattr(self, 'url_options'):
            if self.url_options.get('cleanoutput'):
                common_params['cleanoutput'] = "1"
            if self.url_options.get('showlabels'):
                common_params['showlabels'] = None

        # Process each player
        player_info = self.player_info.get("1.0", tk.END)
        for i, line in enumerate(player_info.split('\n')):
            line = line.strip()
            if not line:
                continue
            
            try:
                username, char_name = [x.strip() for x in line.split(',', 1)]
                display_name = f"{username}/{char_name}"
                
                # Generate unique push ID for this player
                player_push_id = self.generate_permanent_id(f"{room_name}_{username}_{char_name}")
                
                # Room link (where they push their stream)
                player_room_params = common_params.copy()
                player_room_params.update({
                    "push": player_push_id,
                    "name": username,
                    "label": display_name,
                    "effects": None  # Add effects parameter for guest controls
                })

                # Handle password for player links
                if include_password:
                    player_room_params["password"] = password
                else:
                    player_room_params["requirepassword"] = None

                # Special URL handling for parameters without values
                player_room_link = base_url + "&".join(k if v is None else f"{k}={v}" for k, v in player_room_params.items())
                
                LinkButton(self.links_frame.scrollable_frame, 
                          player_room_link, 
                          f"Room Link: {display_name}").pack(fill="x")
                
                # Store player info for OBS updates
                solo_params = {
                    "view": player_push_id,
                    "solo": None,
                    "room": room_name,
                    "effects": None
                }
                
                if include_password:
                    solo_params["password"] = password
                else:
                    solo_params["requirepassword"] = None
                
                # Generate solo link with consistent parameter handling
                solo_link = base_url + "&".join(k if v is None else f"{k}={v}" for k, v in solo_params.items())
                
                self.player_sources.append({
                    'name_source': f"p{i}name",
                    'browser_source': f"p{i}vdosolo",
                    'display_name': display_name,
                    'solo_link': solo_link
                })
                
                self.player_links.append({
                    'display_name': display_name,
                    'room_link': player_room_link
                })
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid player info format for line: {line}\nExpected format: username,character_name")
                continue
        
        # Add control buttons frame at the bottom
        control_frame = ttk.Frame(self.links_frame.scrollable_frame)
        control_frame.pack(fill="x", pady=20)
        
        # Update All OBS Sources button
        update_all_btn = ttk.Button(control_frame, 
                                  text="Update All OBS Sources",
                                  command=self.update_all_sources,
                                  width=30)
        update_all_btn.pack(pady=5)
        
        # Copy HTML Links button
        copy_html_btn = ttk.Button(control_frame,
                                 text="Copy HTML Player Links",
                                 command=self.copy_html_links,
                                 width=30)
        copy_html_btn.pack(pady=5)
        
        # Copy Plain Text Links button
        copy_text_btn = ttk.Button(control_frame,
                                 text="Copy Plain Text Links",
                                 command=self.copy_text_links,
                                 width=30)
        copy_text_btn.pack(pady=5)
        
        self.save_config()

    def copy_html_links(self):
        """Generate HTML formatted links for all players and copy to clipboard"""
        html_lines = ["<ul>"]
        for player in self.player_links:
            short_url = player["room_link"]
            html_lines.append(f'  <li>{player["display_name"]}: <a href="{short_url}">{short_url}</a></li>')
        html_lines.append("</ul>")
        
        html_content = "\n".join(html_lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(html_content)
        messagebox.showinfo("Success", "HTML player links copied to clipboard")

    def copy_text_links(self):
        """Generate plain text formatted links for all players and copy to clipboard"""
        text_lines = []
        for player in self.player_links:
            short_url = player["room_link"]
            text_lines.append(f'{player["display_name"]}: {short_url}')
        
        text_content = "\n".join(text_lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text_content)
        messagebox.showinfo("Success", "Plain text player links copied to clipboard")

    def update_obs_source(self, ws, input_name, settings):
        """Helper function to update an OBS source with given settings"""
        sources = ws.call(requests.GetInputList())
        all_sources = {s['inputName']: s['unversionedInputKind'] for s in sources.datain['inputs']}
        logger.debug(f"Attempting to update source '{input_name}' with settings {settings}")
        
        if input_name not in all_sources:
            error_msg = f"Source '{input_name}' not found in OBS. Available sources: {list(all_sources.keys())}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return False
            
        response = ws.call(requests.SetInputSettings(inputName=input_name, inputSettings=settings))
        logger.debug(f"Response from OBS for {input_name}: {response}")
        return True

    def update_all_sources(self):
        """Update all OBS text and browser sources at once"""
        try:
            # Connect to OBS WebSocket
            logger.debug("Connecting to OBS WebSocket...")
            ws = obsws("localhost", 4455, "Truff1es")
            ws.connect()
            logger.info("Connected to OBS WebSocket")
            
            # Update each player's sources
            for source in self.player_sources:
                # Update name source
                name_settings = {"text": source['display_name']}
                self.update_obs_source(ws, source['name_source'], name_settings)
                
                # Update browser source
                browser_settings = {"url": source['solo_link']}
                self.update_obs_source(ws, source['browser_source'], browser_settings)
            
            ws.disconnect()
            logger.info("Disconnected from OBS WebSocket")
            
            messagebox.showinfo("Success", "All OBS sources updated successfully")
            
        except Exception as e:
            error_msg = f"Failed to update OBS sources: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)

    def save_config(self):
        """Save current configuration to JSON file"""
        config = {
            "room_name": self.room_name.get(),
            "host_username": self.host_username.get(),
            "host_character": self.host_character.get(),
            "room_password": self.room_password.get(),
            "password_inclusion": self.password_inclusion.get(),
            "player_info": self.player_info.get("1.0", tk.END)
        }
        try:
            with open("room_config.json", 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")

    def show_room_dialog(self, operation='load'):
        """Show a dialog for room operations (load/save/save as)
        operation: One of 'load', 'save', 'save_as'
        """
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.transient(self.root)
        dialog.grab_set()
        
        if operation == 'load':
            dialog.title("Load Room")
            prompt_text = "Select a room to load:"
        elif operation == 'save':
            dialog.title("Save Room")
            prompt_text = "Save current room or select existing room to overwrite:"
        else:  # save_as
            dialog.title("Save Room As")
            prompt_text = "Enter new room name or select existing room to overwrite:"
            
        dialog.geometry("400x500")
        
        # Main container with padding
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Room name entry
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(name_frame, text="Room Name:").pack(side="left")
        name_entry = ttk.Entry(name_frame)
        name_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # If we have a current room name, use it
        if self.room_name.get():
            name_entry.insert(0, self.room_name.get())
        
        # Existing rooms section
        ttk.Label(main_frame, text=prompt_text).pack(anchor="w")
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(5, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox with existing rooms
        room_files = [f for f in os.listdir('.') if f.endswith('_room.json')]
        for room_file in room_files:
            room_name = room_file[:-10]  # Remove _room.json
            listbox.insert("end", room_name)
        
        def on_select(event):
            if listbox.curselection():
                selected = listbox.get(listbox.curselection())
                name_entry.delete(0, tk.END)
                name_entry.insert(0, selected)
        
        listbox.bind('<<ListboxSelect>>', on_select)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 5))
        
        def do_operation():
            room_name = name_entry.get().strip()
            if not room_name:
                messagebox.showerror("Error", "Please enter a room name")
                return
                
            if operation == 'load':
                filename = f"{room_name}_room.json"
                if not os.path.exists(filename):
                    messagebox.showerror("Error", f"Room '{room_name}' does not exist")
                    return
                    
                try:
                    with open(filename, 'r') as f:
                        room_data = json.load(f)
                    
                    # Update UI with loaded data
                    self.room_name.set(room_data['room_name'])
                    self.host_username.delete(0, tk.END)
                    self.host_username.insert(0, room_data['host_username'])
                    self.host_character.delete(0, tk.END)
                    self.host_character.insert(0, room_data['host_character'])
                    self.room_password.delete(0, tk.END)
                    self.room_password.insert(0, room_data['room_password'])
                    self.password_inclusion.set(room_data.get("password_inclusion", "include"))
                    self.player_info.delete("1.0", tk.END)
                    self.player_info.insert("1.0", room_data['player_info'])
                    
                    self.current_room_name = room_data['room_name']
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Room {room_name} loaded")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load room: {str(e)}")
            else:  # save or save_as
                filename = f"{room_name}_room.json"
                if os.path.exists(filename) and not messagebox.askyesno("Confirm Overwrite", 
                    f"Room '{room_name}' already exists. Do you want to overwrite it?"):
                    return
                    
                room_data = {
                    'room_name': room_name,
                    'host_username': self.host_username.get(),
                    'host_character': self.host_character.get(),
                    'room_password': self.room_password.get(),
                    'password_inclusion': self.password_inclusion.get(),
                    'player_info': self.player_info.get("1.0", tk.END)
                }
                
                try:
                    with open(filename, 'w') as f:
                        json.dump(room_data, f, indent=4)
                    self.room_name.set(room_name)
                    self.current_room_name = room_name
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Room saved as {filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save room: {str(e)}")
        
        def cancel_operation():
            dialog.destroy()
        
        ttk.Button(button_frame, 
                  text="OK" if operation == 'load' else "Save",
                  command=do_operation).pack(side="left", padx=5)
        ttk.Button(button_frame, 
                  text="Cancel",
                  command=cancel_operation).pack(side="left")
        
        # Center the dialog on the screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make dialog modal
        dialog.focus_set()
        dialog.wait_window()

    def save_room(self):
        """Save current room configuration to JSON file"""
        if not self.room_name.get():
            messagebox.showerror("Error", "Please enter a room name")
            return
        self.show_room_dialog('save')
    
    def save_room_as(self):
        """Save current room configuration with a new name"""
        self.show_room_dialog('save_as')
    
    def load_room(self):
        """Load room configuration from JSON file"""
        self.show_room_dialog('load')
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open("room_config.json", "r") as f:
                config = json.load(f)
                if config:
                    self.room_name.set(config.get("room_name", ""))
                    self.host_username.delete(0, tk.END)
                    self.host_username.insert(0, config.get("host_username", ""))
                    self.host_character.delete(0, tk.END)
                    self.host_character.insert(0, config.get("host_character", ""))
                    self.room_password.delete(0, tk.END)
                    self.room_password.insert(0, config.get("room_password", ""))
                    self.password_inclusion.set(config.get("password_inclusion", "include"))
                    self.player_info.delete("1.0", tk.END)
                    self.player_info.insert("1.0", config.get("player_info", ""))
        except:
            pass

    def show_url_options(self):
        """Show dialog for configuring VDO.Ninja URL options"""
        dialog = tk.Toplevel(self.root)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.title("VDO.Ninja URL Options")
        dialog.geometry("600x700")
        
        # Main container with padding
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Create a notebook for tabbed organization
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Video Options Tab
        video_frame = ttk.Frame(notebook, padding="10")
        notebook.add(video_frame, text="Video")
        
        # Resolution options
        res_frame = ttk.LabelFrame(video_frame, text="Resolution", padding="5")
        res_frame.pack(fill="x", pady=(0, 10))
        
        self.resolution_var = tk.StringVar(value="1080")
        resolutions = [
            ("4K (2160p)", "2160"),
            ("1440p", "1440"),
            ("1080p", "1080"),
            ("720p", "720"),
            ("480p", "480")
        ]
        for text, value in resolutions:
            ttk.Radiobutton(res_frame, text=text, value=value, 
                          variable=self.resolution_var).pack(anchor="w")
        
        # Video quality options
        quality_frame = ttk.LabelFrame(video_frame, text="Quality Settings", padding="5")
        quality_frame.pack(fill="x", pady=(0, 10))
        
        self.bitrate_var = tk.StringVar(value="")
        bitrate_frame = ttk.Frame(quality_frame)
        bitrate_frame.pack(fill="x")
        ttk.Label(bitrate_frame, text="Bitrate (kbps):").pack(side="left")
        ttk.Entry(bitrate_frame, textvariable=self.bitrate_var, width=10).pack(side="left", padx=5)
        CreateToolTip(bitrate_frame, "Set target video bitrate in kbps (e.g., 4000)")
        
        self.fps_var = tk.StringVar(value="30")
        fps_frame = ttk.Frame(quality_frame)
        fps_frame.pack(fill="x", pady=5)
        ttk.Label(fps_frame, text="FPS:").pack(side="left")
        ttk.Combobox(fps_frame, textvariable=self.fps_var, values=["24", "30", "60"], width=7).pack(side="left", padx=5)
        CreateToolTip(fps_frame, "Set target frame rate")
        
        # Interface Options Tab
        interface_frame = ttk.Frame(notebook, padding="10")
        notebook.add(interface_frame, text="Interface")
        
        # Interface options
        interface_options_frame = ttk.LabelFrame(interface_frame, text="Interface Options", padding="5")
        interface_options_frame.pack(fill="x", pady=(0, 10))
        
        self.cleanoutput_var = tk.BooleanVar(value=False)
        clean_frame = ttk.Frame(interface_options_frame)
        clean_frame.pack(fill="x", pady=2)
        ttk.Checkbutton(clean_frame, text="Clean Output (Hide UI Elements)", variable=self.cleanoutput_var).pack(side="left")
        CreateToolTip(clean_frame, "Remove UI elements for a cleaner output. Note: This will hide the control bar.")

        self.showlabels_var = tk.BooleanVar(value=False)
        labels_frame = ttk.Frame(interface_options_frame)
        labels_frame.pack(fill="x", pady=2)
        ttk.Checkbutton(labels_frame, text="Show Labels", variable=self.showlabels_var).pack(side="left")
        CreateToolTip(labels_frame, "Show participant labels in the video feed")
        
        # Audio Options Tab
        audio_frame = ttk.Frame(notebook, padding="10")
        notebook.add(audio_frame, text="Audio")
        
        audio_quality_frame = ttk.LabelFrame(audio_frame, text="Audio Settings", padding="5")
        audio_quality_frame.pack(fill="x", pady=(0, 10))
        
        self.audio_bitrate_var = tk.StringVar(value="")
        audio_bitrate_frame = ttk.Frame(audio_quality_frame)
        audio_bitrate_frame.pack(fill="x")
        ttk.Label(audio_bitrate_frame, text="Audio Bitrate (kbps):").pack(side="left")
        ttk.Entry(audio_bitrate_frame, textvariable=self.audio_bitrate_var, width=10).pack(side="left", padx=5)
        CreateToolTip(audio_bitrate_frame, "Set target audio bitrate in kbps (e.g., 128)")
        
        # Feature Toggles Tab
        features_frame = ttk.Frame(notebook, padding="10")
        notebook.add(features_frame, text="Features")
        
        # Create scrollable frame for features
        features_canvas = tk.Canvas(features_frame)
        scrollbar = ttk.Scrollbar(features_frame, orient="vertical", command=features_canvas.yview)
        scrollable_frame = ttk.Frame(features_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: features_canvas.configure(scrollregion=features_canvas.bbox("all"))
        )
        
        features_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        features_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Common feature toggles
        self.feature_vars = {}
        features = [
            ("meshcast", "Use mesh networking for improved performance"),
            ("webcam", "Enable webcam"),
            ("screen", "Enable screen sharing"),
            ("autostart", "Auto-start camera/mic on join"),
            ("muted", "Start muted"),
            ("videomuted", "Start with video muted"),
            ("chat", "Enable text chat"),
            ("stereo", "Enable stereo audio"),
            ("noise", "Enable noise suppression")
        ]
        
        for feature, description in features:
            var = tk.BooleanVar(value=False)
            self.feature_vars[feature] = var
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            ttk.Checkbutton(frame, text=feature, variable=var).pack(side="left")
            CreateToolTip(frame, description)
        
        features_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Advanced Options Tab
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced")
        
        # Advanced settings
        self.advanced_vars = {}
        advanced_settings = [
            ("codec", "Video Codec", ["VP8", "VP9", "H264", "AV1"]),
            ("audiocodec", "Audio Codec", ["OPUS", "AAC"]),
            ("keyframerate", "Keyframe Interval", ["1", "2", "4", "10"]),
        ]
        
        for setting, label, options in advanced_settings:
            frame = ttk.Frame(advanced_frame)
            frame.pack(fill="x", pady=5)
            ttk.Label(frame, text=label + ":").pack(side="left")
            var = tk.StringVar()
            self.advanced_vars[setting] = var
            ttk.Combobox(frame, textvariable=var, values=options, width=15).pack(side="left", padx=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def apply_options():
            # Store all options in a dictionary
            self.url_options = {
                'resolution': self.resolution_var.get(),
                'bitrate': self.bitrate_var.get(),
                'fps': self.fps_var.get(),
                'audio_bitrate': self.audio_bitrate_var.get(),
                'cleanoutput': self.cleanoutput_var.get(),
                'showlabels': self.showlabels_var.get(),
                'features': {k: v.get() for k, v in self.feature_vars.items()},
                'advanced': {k: v.get() for k, v in self.advanced_vars.items()}
            }
            dialog.destroy()
            
        def reset_options():
            # Reset all options to defaults
            self.resolution_var.set("1080")
            self.bitrate_var.set("")
            self.fps_var.set("30")
            self.audio_bitrate_var.set("")
            self.cleanoutput_var.set(False)
            self.showlabels_var.set(False)
            for var in self.feature_vars.values():
                var.set(False)
            for var in self.advanced_vars.values():
                var.set("")
        
        ttk.Button(button_frame, text="Apply", command=apply_options).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reset", command=reset_options).pack(side="left")
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Make dialog modal
        dialog.focus_set()
        dialog.wait_window()

def main():
    root = tk.Tk()
    app = VDONinjaManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
