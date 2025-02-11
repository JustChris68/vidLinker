class VDONinjaManager:
    def __init__(self):
        self.base_url = "https://vdo.ninja"
        
    def generate_host_link(self, room_name, password, username, include_password=True):
        """Generate a host link for VDO.Ninja"""
        params = {
            "director": room_name,  # Use director instead of room for host
            "meshcast": "1",
            "username": username,
            "quality": "1080",
            "obs": "1",
            "api": "1"
        }
        
        if include_password and password:
            params["password"] = password
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/?{query_string}"
        
    def generate_player_link(self, room_name, password, username, include_password=True):
        """Generate a player link for VDO.Ninja"""
        params = {
            "room": room_name,
            "meshcast": "1",
            "username": username,
            "quality": "1080"
        }
        
        if include_password and password:
            params["password"] = password
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/?{query_string}"
        
    def generate_solo_link(self, room_name, password, username, include_password=True):
        """Generate a solo link for VDO.Ninja"""
        params = {
            "room": room_name,
            "view": username,
            "meshcast": "1",
            "quality": "1080"
        }
        
        if include_password and password:
            params["password"] = password
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.base_url}/?{query_string}"

    def generate_link(self, username: str, character: str = None, is_host: bool = False) -> str:
        """Generate a VDO.Ninja link for a player or host"""
        try:
            base_url = "https://vdo.ninja"
            params = []
            
            # Add room parameters
            if self.settings.room.room_name:
                params.append(f"room={self.settings.room.room_name}")
                
            if self.settings.room.room_password and self.settings.room.include_password:
                params.append(f"password={self.settings.room.room_password}")
            
            # Add video parameters
            if self.settings.video.resolution:
                params.append(f"quality={self.settings.video.resolution}")
            
            if self.settings.video.bitrate:
                params.append(f"bitrate={self.settings.video.bitrate}")
            
            # Add audio parameters
            if self.settings.audio.stereo:
                params.append("stereo")
            
            if self.settings.audio.noise_suppression:
                params.append("denoise")
            
            if self.settings.audio.echo_cancellation:
                params.append("echocancellation")
            
            # Add user parameters
            if username:
                params.append(f"push={username}")
            
            if character:
                params.append(f"label={character}")
            
            # Add host-specific parameters
            if is_host:
                params.append("director=1")
                params.append("scene")
                
                if self.settings.room.obs_control:
                    params.append("obscontrol")
            
            # Build final URL
            query_string = "&".join(params)
            return f"{base_url}/?{query_string}"
            
        except Exception as e:
            raise Exception(f"Failed to generate VDO.Ninja link: {str(e)}")
