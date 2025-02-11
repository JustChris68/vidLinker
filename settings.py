from dataclasses import dataclass, asdict, field
import json
import os
from typing import Optional, Dict

@dataclass
class InterfaceSettings:
    """Interface settings"""
    show_labels: bool = True
    clean_output: bool = False
    debug_mode: bool = False
    enable_obs: bool = False  # Added OBS enable toggle

@dataclass
class VideoSettings:
    """Video settings"""
    resolution: str = "1080p"
    bitrate: str = ""
    fps: str = ""

@dataclass
class AudioSettings:
    """Audio settings"""
    bitrate: str = ""
    stereo: bool = False
    noise_suppression: bool = True

@dataclass
class OBSSettings:
    """OBS connection settings"""
    host: str = "localhost"
    port: int = 4455  # Updated to OBS 28+ default port
    password: Optional[str] = None

@dataclass
class RoomSettings:
    """Room settings"""
    room_name: str = ""
    host_username: str = ""
    host_character: str = ""
    room_password: str = ""
    password_inclusion: str = "include"
    player_info: str = ""
    players: Dict[str, str] = field(default_factory=dict)  # name -> character mapping
    
    def get_config(self):
        """Get configuration as dictionary"""
        # Convert player_info to players dict if needed
        if self.player_info and not self.players:
            for line in self.player_info.splitlines():
                if line.strip():
                    try:
                        username, character = map(str.strip, line.split(','))
                        self.players[username] = character
                    except ValueError:
                        continue
        
        return {
            "room": self.room_name,
            "password": self.room_password,
            "players": self.players
        }
    
    def set_config(self, config):
        """Set configuration from dictionary"""
        self.room_name = config.get("room", "")
        self.room_password = config.get("password", "")
        self.players = config.get("players", {})
        
        # Update player_info for backward compatibility
        self.player_info = "\n".join(f"{name},{char}" for name, char in self.players.items())
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def from_dict(self, data):
        """Load from dictionary"""
        # Handle old format
        if "room_name" in data:
            self.room_name = data["room_name"]
            self.room_password = data.get("room_password", "")
            self.host_username = data.get("host_username", "")
            self.host_character = data.get("host_character", "")
            self.password_inclusion = data.get("password_inclusion", "include")
            self.player_info = data.get("player_info", "")
            
            # Convert player_info to players dict
            self.players = {}
            if self.player_info:
                for line in self.player_info.splitlines():
                    if line.strip():
                        try:
                            username, character = map(str.strip, line.split(','))
                            self.players[username] = character
                        except ValueError:
                            continue
        # Handle new format
        else:
            self.room_name = data.get("room", "")
            self.room_password = data.get("password", "")
            self.players = data.get("players", {})
            # Update player_info for backward compatibility
            self.player_info = "\n".join(f"{name},{char}" for name, char in self.players.items())
    
    def get_host_link(self):
        """Generate the host/director link"""
        params = {
            "director": self.room_name,
            "meshcast": "1",
            "username": self.host_username or "Host",
            "quality": "1080",
            "obs": "1",
            "api": "1",
            "password": self.room_password
        }
        return "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in params.items())
    
    def get_player_link(self, player_name):
        """Generate a player link"""
        params = {
            "room": self.room_name,
            "meshcast": "1",
            "username": player_name,
            "quality": "1080",
            "password": self.room_password
        }
        return "https://vdo.ninja/?" + "&".join(f"{k}={v}" for k, v in params.items())

class Settings:
    """Application settings"""
    def __init__(self):
        self.interface = InterfaceSettings()
        self.video = VideoSettings()
        self.audio = AudioSettings()
        self.obs = OBSSettings()
        self.room = RoomSettings()
    
    def save(self, file_path: str = None):
        """Save settings to a file"""
        if file_path is None:
            file_path = 'settings.json'
            
        try:
            settings_data = {
                'interface': asdict(self.interface),
                'video': asdict(self.video),
                'audio': asdict(self.audio),
                'obs': asdict(self.obs),
                'room': asdict(self.room)
            }
            with open(file_path, 'w') as f:
                json.dump(settings_data, f, indent=4)
        except Exception as e:
            raise Exception(f"Failed to save settings: {str(e)}")
    
    def save_room(self, file_path: str):
        """Save room configuration to a specific file"""
        try:
            room_data = asdict(self.room)
            with open(file_path, 'w') as f:
                json.dump(room_data, f, indent=4)
        except Exception as e:
            raise Exception(f"Failed to save room configuration: {str(e)}")
    
    def load(self):
        """Load settings from file"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                    
                    # Load interface settings
                    if 'interface' in data:
                        for k, v in data['interface'].items():
                            setattr(self.interface, k, v)
                    
                    # Load video settings
                    if 'video' in data:
                        for k, v in data['video'].items():
                            setattr(self.video, k, v)
                    
                    # Load audio settings
                    if 'audio' in data:
                        for k, v in data['audio'].items():
                            setattr(self.audio, k, v)
                    
                    # Load OBS settings
                    if 'obs' in data:
                        for k, v in data['obs'].items():
                            setattr(self.obs, k, v)
                    
                    # Load room settings
                    if 'room' in data:
                        for k, v in data['room'].items():
                            setattr(self.room, k, v)
        except Exception as e:
            print(f"Failed to load settings: {str(e)}")
            # Use defaults if loading fails
            self.__init__()
