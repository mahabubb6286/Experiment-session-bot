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

        # Runtime-only 2FA settings
        self.use_2fa = False
        self.custom_2fa_password = None

        # Runtime-only whitelist (Stores ISO codes, e.g. ['BD', 'US', 'CA'])
        self.allowed_countries = []

        # Load Device Data
        with open("devices.json", "r", encoding="utf-8") as f:
            self.devices_list = json.load(f)

        # Load Countries Database
        with open("countries.json", "r", encoding="utf-8") as f:
            self.countries_db = json.load(f)

    def get_random_device(self):
        return random.choice(self.devices_list)

    def format_phone_number(self, phone_str: str) -> str:
        phone_str = phone_str.strip()
        if not phone_str.startswith("+"):
            phone_str = "+" + phone_str
        return phone_str

    def get_country_info(self, phone_number: str):
        """Area Code (US/Canada etc.) সহ নির্ভুল দেশ ডিটেক্ট করার জন্য phonenumbers ব্যবহার করা হয়েছে"""
        try:
            formatted_phone = self.format_phone_number(phone_number)
            parsed = phonenumbers.parse(formatted_phone, None)
            if not phonenumbers.is_valid_number(parsed):
                return None
            country_iso = phonenumbers.region_code_for_number(parsed)
            
            # Match with countries.json
            for c in self.countries_db:
                if c["code"].upper() == country_iso.upper():
                    return c
        except Exception:
            pass
        return None

    def search_country_for_whitelist(self, query: str):
        """Full name, ISO code, dial code—তিনভাবেই দেশ খোঁজার স্মার্ট মেথড"""
        query_clean = query.strip().lower()
        if query_clean.startswith("+"):
            dial_query = query_clean
        else:
            dial_query = "+" + query_clean

        matched = []
        for c in self.countries_db:
            if (query_clean == c["name"].lower() or 
                query_clean == c["code"].lower() or 
                query_clean == c["dial_code"].lower() or 
                dial_query == c["dial_code"].lower()):
                matched.append(c)
        return matched

    def is_country_allowed(self, phone_number: str) -> bool:
        c_info = self.get_country_info(phone_number)
        if c_info:
            return c_info["code"].upper() in [x.upper() for x in self.allowed_countries]
        return False

    def get_country_proxy(self, phone_number: str):
        c_info = self.get_country_info(phone_number)
        country_code = c_info["code"].lower() if c_info else "us"
        targeted_user = f"{self.proxy_user}_cr.{country_code}"

        return {
            "scheme": "socks5",
            "hostname": self.proxy_host,
            "port": self.proxy_port,
            "username": targeted_user,
            "password": self.proxy_pass
        }
