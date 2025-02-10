class URLManager:
    """Handles all URL-related operations for VDO.Ninja links"""
    
    BASE_URL = "https://vdo.ninja/?"
    
    @staticmethod
    def generate_room_name(host: str, password: str) -> str:
        """Generate a consistent room name from host and password"""
        return f"vidlinker_{host}_{password}"
    
    @staticmethod
    def build_url(params: dict) -> str:
        """Build a URL from parameters, handling None values as standalone parameters"""
        param_strings = []
        for k, v in params.items():
            if v is None:
                param_strings.append(k)
            else:
                param_strings.append(f"{k}={v}")
        return URLManager.BASE_URL + "&".join(param_strings)
    
    @staticmethod
    def get_common_params(room_name: str) -> dict:
        """Get common parameters used in all links"""
        return {
            "room": room_name,
            "meshcast": "1",
            "quality": "1080"
        }
    
    @staticmethod
    def get_host_params(room_name: str, password: str, host: str, host_character: str) -> dict:
        """Get parameters specific to host/director links"""
        return {
            "room": room_name,
            "password": password,
            "director": None,
            "name": host,
            "label": f"{host}/{host_character}"
        }
    
    @staticmethod
    def get_player_params(room_name: str, password: str, username: str, display_name: str, 
                         player_push_id: str, include_password: bool) -> dict:
        """Get parameters specific to player links"""
        params = {
            "room": room_name,
            "push": player_push_id,
            "name": username,
            "label": display_name,
            "effects": None
        }
        
        if include_password:
            params["password"] = password
        else:
            params["requirepassword"] = None
            
        return params
    
    @staticmethod
    def get_solo_params(room_name: str, password: str, player_push_id: str, include_password: bool) -> dict:
        """Get parameters specific to solo/OBS links"""
        params = {
            "view": player_push_id,
            "solo": None,
            "room": room_name,
            "effects": None
        }
        
        if include_password:
            params["password"] = password
        else:
            params["requirepassword"] = None
            
        return params
