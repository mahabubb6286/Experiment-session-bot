import os
import json
import random
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

class ConfigEngine:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID", "0"))
        self.api_hash = os.getenv("API_HASH")
        self.bot_token = os.getenv("BOT_TOKEN")
        self.admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        
        # Proxy Details
        self.proxy_host = os.getenv("PROXY_HOST", "gw.dataimpulse.com")
        self.proxy_port = int(os.getenv("PROXY_PORT", 823))
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")

        # Dynamic 2FA Settings (Controlled via Admin Panel)
        self.use_2fa = True
        self.custom_2fa_password = "Default2FA@123"
        
        # Allowed Countries (ISO Codes)
        self.allowed_countries = ["BD", "US", "CL", "IN", "AR"]

        with open("devices.json", "r") as f:
            self.devices_list = json.load(f)

    def get_random_device(self):
        return random.choice(self.devices_list)

    def get_country_info(self, phone_number: str):
        try:
            parsed = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed):
                return None
            country_code = phonenumbers.region_code_for_number(parsed)
            return country_code.upper() if country_code else None
        except Exception:
            return None

    def is_country_allowed(self, phone_number: str) -> bool:
        country = self.get_country_info(phone_number)
        return country in self.allowed_countries if country else False

    def get_country_proxy(self, phone_number: str):
        country = self.get_country_info(phone_number)
        country_code = country.lower() if country else "us"
        targeted_user = f"{self.proxy_user}_cr.{country_code}"

        return {
            "scheme": "socks5",
            "hostname": self.proxy_host,
            "port": self.proxy_port,
            "username": targeted_user,
            "password": self.proxy_pass
        }
