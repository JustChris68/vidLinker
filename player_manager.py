from dataclasses import dataclass
from typing import List, Optional
import hashlib

@dataclass
class Player:
    """Represents a player in the VDO.Ninja room"""
    username: str
    character_name: str
    push_id: str
    room_link: Optional[str] = None
    solo_link: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Get the display name in format username/character"""
        return f"{self.username}/{self.character_name}"

@dataclass
class OBSSource:
    """Represents an OBS source for a player"""
    name_source: str
    browser_source: str
    display_name: str
    solo_link: str

class PlayerManager:
    """Manages players and their associated links/sources"""
    
    def __init__(self):
        self.players: List[Player] = []
        self.obs_sources: List[OBSSource] = []
    
    def clear(self) -> None:
        """Clear all player data"""
        self.players.clear()
        self.obs_sources.clear()
    
    @staticmethod
    def generate_push_id(room_name: str, username: str, char_name: str) -> str:
        """Generate a permanent, unique push ID for a player"""
        seed = f"{room_name}_{username}_{char_name}"
        return hashlib.md5(seed.encode()).hexdigest()[:8]
    
    def parse_player_info(self, player_info: str) -> List[Player]:
        """Parse player information from text input"""
        players = []
        for line in player_info.splitlines():
            line = line.strip()
            if not line:
                continue
                
            try:
                username, char_name = [x.strip() for x in line.split(',', 1)]
                player = Player(
                    username=username,
                    character_name=char_name,
                    push_id=""  # Will be set when generating links
                )
                players.append(player)
            except ValueError:
                continue  # Skip invalid lines
                
        return players
    
    def create_obs_source(self, player: Player, index: int) -> OBSSource:
        """Create OBS source information for a player"""
        return OBSSource(
            name_source=f"p{index}name",
            browser_source=f"p{index}vdosolo",
            display_name=player.display_name,
            solo_link=player.solo_link or ""
        )
    
    def update_player_links(self, players: List[Player]) -> None:
        """Update the internal player list and create OBS sources"""
        self.players = players
        self.obs_sources.clear()
        
        for i, player in enumerate(self.players):
            if player.solo_link:  # Only create OBS source if links are set
                self.obs_sources.append(self.create_obs_source(player, i))
