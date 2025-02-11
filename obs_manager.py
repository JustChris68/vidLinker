from typing import Optional, Dict, Any
from obswebsocket import obsws, requests, exceptions
import logging
import re

class OBSManager:
    """Manages OBS WebSocket connection and source updates"""
    
    def __init__(self):
        self.ws = None
        self.connected = False
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        handler = logging.FileHandler('obs_debug.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def connect(self, host: str = "localhost", port: int = 4444, password: Optional[str] = None) -> bool:
        """Connect to OBS WebSocket"""
        try:
            self.logger.info(f"Attempting to connect to OBS at {host}:{port}")
            
            # Create WebSocket client and connect
            self.ws = obsws(host=host, port=port, password=password)
            self.ws.connect()
            
            # Test connection by getting version
            version = self.ws.call(requests.GetVersion())
            self.logger.info(f"Connected to OBS {version.getObsVersion()}")
            
            self.connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {str(e)}")
            self.connected = False
            self.ws = None
            raise
    
    def disconnect(self):
        """Disconnect from OBS WebSocket"""
        try:
            if self.ws:
                self.ws.disconnect()
                self.logger.info("Disconnected from OBS WebSocket")
        except Exception as e:
            self.logger.error(f"Error disconnecting from OBS: {str(e)}")
        finally:
            self.connected = False
            self.ws = None
    
    def is_connected(self) -> bool:
        """Check if connected to OBS"""
        try:
            if not self.ws:
                self.connected = False
                return False
                
            # Test connection by getting version
            try:
                version = self.ws.call(requests.GetVersion())
                self.connected = True
                return True
            except:
                self.connected = False
                self.ws = None
                return False
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            self.connected = False
            self.ws = None
            return False
    
    def update_text_source(self, source_name: str, text: str) -> bool:
        """Update an OBS text source"""
        if not self.connected or not self.ws:
            return False
            
        try:
            self.ws.call(requests.SetTextGDIPlusProperties(source=source_name, text=text))
            return True
        except Exception as e:
            self.logger.error(f"Failed to update text source {source_name}: {str(e)}")
            return False
    
    def update_browser_source(self, source_name: str, url: str) -> bool:
        """Update an OBS browser source"""
        if not self.connected or not self.ws:
            return False
            
        try:
            settings = {"url": url}
            self.ws.call(requests.SetSourceSettings(sourceName=source_name, sourceSettings=settings))
            return True
        except Exception as e:
            self.logger.error(f"Failed to update browser source {source_name}: {str(e)}")
            return False
    
    def update_sources(self, links: Dict[str, str]) -> None:
        """Update OBS sources with current links"""
        try:
            if not self.ws or not self.connected:
                self.logger.error("Not connected to OBS")
                return
                
            self.logger.info("Checking if VDO Assets scene exists...")
            
            # Get or create VDO Assets scene
            scene_name = "VDO Assets"
            self._get_or_create_scene(scene_name)
            
            # Process host source
            self.logger.info("Processing host source...")
            self._update_host_source(links['director'])
            
            # Process player sources
            player_num = 1
            for username, link in links.items():
                if username != "director":
                    self.logger.info(f"Processing player {player_num}...")
                    self._update_player_source(player_num, link)
                    player_num += 1
            
            self.logger.info(f"Successfully updated {player_num - 1} player sources")
            
        except Exception as e:
            self.logger.error(f"Error updating sources: {str(e)}")
            raise
    
    def _get_or_create_scene(self, scene_name: str) -> str:
        """Get or create a scene"""
        try:
            # Get scene list
            scene_list = self.ws.call(requests.GetSceneList())
            scenes = scene_list.getScenes()
            
            # Check if scene exists
            if any(scene['sceneName'] == scene_name for scene in scenes):
                self.logger.info(f"{scene_name} scene already exists")
                return scene_name
            
            # Create scene if it doesn't exist
            self.ws.call(requests.CreateScene(sceneName=scene_name))
            self.logger.info(f"Created {scene_name} scene")
            return scene_name
            
        except Exception as e:
            self.logger.error(f"Failed to get or create scene {scene_name}: {str(e)}")
            raise
    
    def _update_host_source(self, link: str) -> None:
        """Update host source"""
        try:
            # Update browser source for host video
            self.update_browser_source("p0vdosolo", link)
            
            # Update text source for host name
            self.update_text_source("p0name", "Host")
            
        except Exception as e:
            self.logger.error(f"Failed to update host source: {str(e)}")
            raise
    
    def _update_player_source(self, player_num: int, link: str) -> None:
        """Update player source"""
        try:
            # Update browser source for player video
            self.update_browser_source(f"p{player_num}vdosolo", link)
            
            # Update text source for player name
            self.update_text_source(f"p{player_num}name", f"Player {player_num}")
            
        except Exception as e:
            self.logger.error(f"Failed to update player {player_num} source: {str(e)}")
            raise
    
    def ensure_scene_exists(self, scene_name: str) -> str:
        """Ensure the specified scene exists, creating it if necessary"""
        try:
            self.logger.info(f"Checking if {scene_name} scene exists...")
            scenes = self.ws.call(requests.GetSceneList())
            scene_exists = any(scene['sceneName'] == scene_name for scene in scenes.getScenes())
            
            if not scene_exists:
                self.logger.info(f"Creating {scene_name} scene...")
                self.ws.call(requests.CreateScene(sceneName=scene_name))
                self.logger.info(f"Successfully created {scene_name} scene")
            else:
                self.logger.debug(f"{scene_name} scene already exists")
            
            return scene_name
            
        except Exception as e:
            self.logger.error(f"Failed to ensure {scene_name} scene exists: {str(e)}")
            raise

    def ensure_source_in_scene(self, source_name: str, scene_name: str) -> None:
        """Ensure a source exists in the specified scene"""
        try:
            self.logger.info(f"Ensuring source {source_name} exists in scene {scene_name}")
            
            # Get scene items
            scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name)).getSceneItems()
            source_in_scene = any(item['sourceName'] == source_name for item in scene_items)
            
            if not source_in_scene:
                self.logger.info(f"Adding source {source_name} to scene {scene_name}")
                # Create a reference to the source in the scene
                self.ws.call(requests.CreateInput(
                    sceneName=scene_name,
                    inputName=source_name,
                    inputKind='browser_source',
                    inputSettings={},
                    sceneItemEnabled=True
                ))
                self.logger.info(f"Successfully added source {source_name} to scene {scene_name}")
            else:
                self.logger.debug(f"Source {source_name} already exists in scene {scene_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure source {source_name} exists in scene {scene_name}: {str(e)}")
            raise

    def ensure_browser_source(self, source_name: str, url: str) -> None:
        """Ensure a browser source exists with the given URL"""
        try:
            settings = {
                "url": url,
                "width": 1920,
                "height": 1080,
                "reroute_audio": True
            }
            
            # Try to get existing source
            try:
                self.ws.call(requests.GetInputSettings(inputName=source_name))
                # Source exists, update it
                self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=settings))
            except:
                # Source doesn't exist, create it
                self.ws.call(requests.CreateInput(
                    sceneName="VDO Assets",
                    inputName=source_name,
                    inputKind="browser_source",
                    inputSettings=settings,
                    sceneItemEnabled=True
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to ensure browser source {source_name}: {str(e)}")
            raise

    def ensure_text_source(self, source_name: str, text: str) -> None:
        """Ensure a text source exists with the given text"""
        try:
            settings = {
                "text": text,
                "font": {
                    "face": "Arial",
                    "size": 32,
                    "style": "Regular"
                },
                "color": 4294967295,  # White
                "outline": True,
                "outline_color": 4278190080,  # Black
                "outline_size": 2
            }
            
            # Try to get existing source
            try:
                self.ws.call(requests.GetInputSettings(inputName=source_name))
                # Source exists, update it
                self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=settings))
            except:
                # Source doesn't exist, create it
                self.ws.call(requests.CreateInput(
                    sceneName="VDO Assets",
                    inputName=source_name,
                    inputKind="text_gdi_plus",
                    inputSettings=settings,
                    sceneItemEnabled=True
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to ensure text source {source_name}: {str(e)}")
            raise

    def update_source(self, source_name: str, settings: dict):
        """Update an OBS source with new settings"""
        if not self.connected:
            self.logger.error(f"Cannot update source {source_name}: Not connected to OBS")
            return
        
        try:
            self.logger.debug(f"Attempting to update source '{source_name}' with settings {settings}")
            response = self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings=settings))
            self.logger.debug(f"Response from OBS for {source_name}: {response}")
        except Exception as e:
            self.logger.error(f"Failed to update source {source_name}: {str(e)}")
            raise
