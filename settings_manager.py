import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class InterfaceSettings:
    """Settings for interface appearance and behavior"""
    show_labels: bool = True
    clean_output: bool = False

@dataclass
class VideoSettings:
    """Settings for video quality and performance"""
    resolution: str = "1080"
    bitrate: str = ""
    fps: str = "30"

@dataclass
class AudioSettings:
    """Settings for audio configuration"""
    bitrate: str = ""
    stereo: bool = False
    noise_suppression: bool = False

@dataclass
class RoomSettings:
    """Settings for room configuration"""
    room_name: str = ""
    host_username: str = ""
    host_character: str = ""
    room_password: str = ""
    password_inclusion: str = "include"
    player_info: str = ""

class SettingsManager:
    """Manages application settings and configuration"""
    
    def __init__(self):
        self.interface = InterfaceSettings()
        self.video = VideoSettings()
        self.audio = AudioSettings()
        self.room = RoomSettings()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all settings to a dictionary"""
        return {
            "interface": asdict(self.interface),
            "video": asdict(self.video),
            "audio": asdict(self.audio),
            "room": asdict(self.room)
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load settings from a dictionary"""
        if "interface" in data:
            self.interface = InterfaceSettings(**data["interface"])
        if "video" in data:
            self.video = VideoSettings(**data["video"])
        if "audio" in data:
            self.audio = AudioSettings(**data["audio"])
        if "room" in data:
            self.room = RoomSettings(**data["room"])
    
    def save_to_file(self, filename: str = "config.json") -> None:
        """Save settings to a JSON file"""
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=4)
    
    def load_from_file(self, filename: str = "config.json") -> None:
        """Load settings from a JSON file"""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                self.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Use defaults if file doesn't exist or is invalid
    
    def save_room(self, filename: Optional[str] = None) -> None:
        """Save room configuration to a JSON file"""
        if filename is None:
            filename = f"{self.room.room_name}_room.json"
        with open(filename, "w") as f:
            json.dump(asdict(self.room), f, indent=4)
    
    def load_room(self, filename: str) -> None:
        """Load room configuration from a JSON file"""
        with open(filename, "r") as f:
            data = json.load(f)
            self.room = RoomSettings(**data)
