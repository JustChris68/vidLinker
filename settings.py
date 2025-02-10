from dataclasses import dataclass, asdict, field
import json
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
    bitrate: str = "2500"
    fps: str = "30"

@dataclass
class AudioSettings:
    """Audio settings"""
    bitrate: str = "128"
    stereo: bool = True
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

@dataclass
class Settings:
    """Application settings"""
    interface: InterfaceSettings = field(default_factory=InterfaceSettings)
    video: VideoSettings = field(default_factory=VideoSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    obs: OBSSettings = field(default_factory=OBSSettings)
    room: RoomSettings = field(default_factory=RoomSettings)
    
    def save(self, filename: str = "settings.json") -> None:
        """Save settings to file"""
        data = {
            "interface": asdict(self.interface),
            "video": asdict(self.video),
            "audio": asdict(self.audio),
            "obs": asdict(self.obs),
            "room": self.room.to_dict()
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    
    def load(self, filename: str = "settings.json") -> None:
        """Load settings from file"""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                
            # Update interface settings
            if "interface" in data:
                self.interface = InterfaceSettings(**data["interface"])
            if "video" in data:
                self.video = VideoSettings(**data["video"])
            if "audio" in data:
                self.audio = AudioSettings(**data["audio"])
            if "obs" in data:
                self.obs = OBSSettings(**data["obs"])
            if "room" in data:
                self.room.from_dict(data["room"])
        except FileNotFoundError:
            # Use defaults if file doesn't exist
            pass
    
    def save_room(self, filename: Optional[str] = None) -> None:
        """Save room configuration"""
        if filename is None:
            filename = f"{self.room.room_name}_room.json"
        
        with open(filename, "w") as f:
            json.dump(self.room.to_dict(), f, indent=4)
    
    def load_room(self, filename: str) -> None:
        """Load room configuration"""
        with open(filename, "r") as f:
            data = json.load(f)
            self.room.from_dict(data)
