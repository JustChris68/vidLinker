from typing import Optional, Dict, Any
from obswebsocket import obsws, requests, exceptions
import logging

class OBSManager:
    """Manages OBS WebSocket connection and source updates"""
    
    def __init__(self):
        self.ws = None
        self.connected = False
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Add file handler
        handler = logging.FileHandler('obs_debug.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
    
    def connect(self, host: str = "localhost", port: int = 4444, password: Optional[str] = None) -> bool:
        """Connect to OBS WebSocket"""
        try:
            self.logger.info(f"Attempting to connect to OBS at {host}:{port}")
            
            if password:
                self.logger.debug("Password provided, attempting authenticated connection")
            
            # Create WebSocket client
            self.ws = obsws(host=host, port=port, password=password)
            self.logger.debug("OBS WebSocket client created, attempting connection...")
            
            # Connect to OBS
            self.ws.connect()
            self.logger.info("Connected to OBS WebSocket")
            
            # Test connection by getting version
            self.logger.debug("Testing connection by getting OBS version...")
            version = self.ws.call(requests.GetVersion())
            self.logger.info(f"Connected to OBS {version.getObsVersion()}")
            
            # Test scene access
            self.logger.debug("Testing scene access...")
            scenes = self.ws.call(requests.GetSceneList())
            self.logger.info(f"Successfully retrieved {len(scenes.getScenes())} scenes")
            for scene in scenes.getScenes():
                self.logger.debug(f"Found scene: {scene['sceneName']}")
            
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
            version = self.ws.call(requests.GetVersion())
            self.connected = True
            return True
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
            self.logger.debug(f"Updated text source {source_name} with text: {text}")
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
            self.logger.debug(f"Updated browser source {source_name} with URL: {url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update browser source {source_name}: {str(e)}")
            return False
    
    def update_all_sources(self, sources: Dict[str, Dict[str, Any]]) -> None:
        """Update multiple OBS sources"""
        if not self.connected:
            return
            
        for source_name, data in sources.items():
            if "text" in data:
                self.update_text_source(source_name, data["text"])
            elif "url" in data:
                self.update_browser_source(source_name, data["url"])
    
    def update_sources(self, links: Dict[str, str]) -> None:
        """Update OBS sources with the provided links"""
        try:
            # Ensure VDO Assets scene exists
            vdo_scene = self.ensure_scene_exists("VDO Assets")
            self.logger.info("Starting source update process...")
            
            # Get current sources
            try:
                scene_items = self.ws.call(requests.GetSceneItemList(sceneName="VDO Assets")).getSceneItems()
                current_sources = {item["sourceName"] for item in scene_items}
                self.logger.debug(f"Current sources in VDO Assets: {', '.join(current_sources)}")
            except Exception as e:
                self.logger.error(f"Failed to get current sources: {str(e)}")
                raise
            
            # Update director/host source
            if "director" in links:
                try:
                    host_source = "p0vdosolo"  # Host is player 0
                    host_name = "p0name"
                    self.logger.info(f"Processing host source: {host_source}")
                    self.logger.debug(f"Host link: {links['director']}")
                    
                    # Create or update browser source
                    self.create_or_update_browser_source(host_source, links["director"])
                    if host_source not in current_sources:
                        self.ensure_source_in_scene(host_source, "VDO Assets")
                    
                    # Create or update text source
                    self.create_or_update_text_source(host_name, "Host")
                    if host_name not in current_sources:
                        self.ensure_source_in_scene(host_name, "VDO Assets")
                except Exception as e:
                    self.logger.error(f"Failed to update host sources: {str(e)}")
                    raise
            
            # Update player sources
            player_count = 1
            for username, link in links.items():
                if username != "director":
                    try:
                        self.logger.info(f"Processing player {player_count}: {username}")
                        
                        # Create source names based on player number
                        vdo_source = f"p{player_count}vdosolo"
                        name_source = f"p{player_count}name"
                        
                        self.logger.debug(f"Creating/updating sources for player {player_count}:")
                        self.logger.debug(f"- Video source: {vdo_source}")
                        self.logger.debug(f"- Name source: {name_source}")
                        
                        # Create or update browser source
                        self.create_or_update_browser_source(vdo_source, link)
                        if vdo_source not in current_sources:
                            self.ensure_source_in_scene(vdo_source, "VDO Assets")
                        
                        # Create or update text source
                        self.create_or_update_text_source(name_source, username)
                        if name_source not in current_sources:
                            self.ensure_source_in_scene(name_source, "VDO Assets")
                        
                        player_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to update sources for player {username}: {str(e)}")
                        raise
            
            self.logger.info(f"Successfully updated {player_count-1} player sources")
            
        except Exception as e:
            self.logger.error(f"Failed to update sources: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                self.logger.error("Traceback:")
                self.logger.error(traceback.format_exc())
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

    def create_or_update_browser_source(self, source_name: str, url: str) -> None:
        """Create or update a browser source with the given URL"""
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
            self.logger.error(f"Failed to create/update browser source {source_name}: {str(e)}")
            raise
    
    def create_or_update_text_source(self, source_name: str, text: str) -> None:
        """Create or update a text source with the given text"""
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
            self.logger.error(f"Failed to create/update text source {source_name}: {str(e)}")
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
