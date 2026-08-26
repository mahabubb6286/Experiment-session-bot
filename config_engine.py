import os
import json
import random
import phonenumbers
from phonenumbers import geocoder
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

        # Custom 2FA & Allowed Countries (Default)
        self.custom_2fa_password = os.getenv("DEFAULT_2FA_PASS", "Default2FA@123")
        self.allowed_countries = ["BD", "US", "CL", "IN", "AR"] # ISO Country Codes (Uppercase)

        # Load Devices
        with open("devices.json", "r") as f:
            self.devices_list = json.load(f)

    def get_random_device(self):
        return random.choice(self.devices_list)

    def get_country_info(self, phone_number: str):
        """নম্বর থেকে ডায়নামিকালি ISO Country Code বের করবে (যেমন: CL, BD, US)"""
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
        """ডায়নামিকালি দেশের প্রক্সি যুক্ত করার লজিক"""
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
