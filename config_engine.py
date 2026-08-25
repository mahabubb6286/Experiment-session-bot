import os
import json
import random
from dotenv import load_dotenv

# .env ফাইল থেকে তথ্য লোড করার জন্য
load_dotenv()

class ConfigEngine:
    def __init__(self):
        self.api_id = int(os.getenv("API_ID", "0"))
        self.api_hash = os.getenv("API_HASH")
        self.bot_token = os.getenv("BOT_TOKEN")
        
        # DataImpulse প্রক্সি ডিটেইলস
        self.proxy_host = os.getenv("PROXY_HOST", "gw.dataimpulse.com")
        self.proxy_port = int(os.getenv("PROXY_PORT", 823))
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")

        # ডিভাইস লিস্ট লোড করা
        with open("devices.json", "r") as f:
            self.devices_list = json.load(f)

    def get_random_device(self):
        """র‍্যান্ডম একটি ডিভাইস প্রোফাইল নিয়ে আসবে"""
        return random.choice(self.devices_list)

    def get_country_proxy(self, phone_number: str):
        """
        নম্বরের Country Code দেখে DataImpulse SOCKS5 Proxy তৈরি করবে
        """
        country_code = "us" # ডিফল্ট ইউএসএ
        if phone_number.startswith("+880"):
            country_code = "bd"
        elif phone_number.startswith("+1"):
            country_code = "us"
        elif phone_number.startswith("+44"):
            country_code = "gb"
        elif phone_number.startswith("+91"):
            country_code = "in"

        # DataImpulse-এর কান্ট্রি ইউজারনেম ফরম্যাট
        targeted_user = f"{self.proxy_user}__country-{country_code}"

        return {
            "scheme": "socks5",
            "hostname": self.proxy_host,
            "port": self.proxy_port,
            "username": targeted_user,
            "password": self.proxy_pass
        }

if __name__ == "__main__":
    print("Config Engine Module Ready!")
