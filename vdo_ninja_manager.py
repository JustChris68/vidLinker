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
