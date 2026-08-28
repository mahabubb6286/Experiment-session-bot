import logging
from database.config_db import get_system_config

logger = logging.getLogger(__name__)

async def get_proxy_dict():
    """Fetches configured proxy settings from database and formats for Pyrogram."""
    try:
        config = await get_system_config()
        
        host = config.get("proxy_host", "").strip()
        port = config.get("proxy_port", "")
        user = config.get("proxy_user", "").strip()
        password = config.get("proxy_pass", "").strip()
        
        if not host or not port:
            return None
        
        proxy_data = {
            "scheme": "socks5",  # Defaulting to SOCKS5 for fast Telegram connectivity
            "hostname": host,
            "port": int(port)
        }
        
        if user and password:
            proxy_data["username"] = user
            proxy_data["password"] = password
            
        return proxy_data
    except Exception as e:
        logger.error(f"Error fetching proxy config: {e}")
        return None
