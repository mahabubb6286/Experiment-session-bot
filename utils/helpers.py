import io
import zipfile
import random
import json
import os
import phonenumbers
from phonenumbers import geocoder
from datetime import datetime
import pytz

def parse_phone_details(phone_number: str):
    """Parses country details from a valid phone number using Google's phonenumbers library."""
    try:
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        
        parsed = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed):
            return None
        
        short_name = phonenumbers.region_code_for_number(parsed)
        full_name = geocoder.country_name_for_number(parsed, "en")
        country_code = f"+{parsed.country_code}"
        
        return {
            "phone": phone_number,
            "short_name": short_name,
            "full_name": full_name,
            "country_code": country_code
        }
    except Exception:
        return None

def get_bd_time():
    """Returns formatted Bangladesh Local Time (UTC+6)."""
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    return now.strftime("%m/%d/%y %H:%M:%S ( Bangladesh (UTC+6) )")

def format_withdraw_report(card_name: str, user_id: int, username: str, balance: float, countries_breakdown: str):
    """Formats withdrawal broadcast report for channels with clickable User ID."""
    formatted_user_id = f"`{user_id}`"
    formatted_username = f"@{username}" if username else "N/A"
    
    report = (
        f"🌳 **𝗡𝗲𝘄 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄 𝗙𝗿𝗼𝗺 {card_name}**\n\n"
        f"👤 **ᴜsᴇʀ ɪᴅ :** {formatted_user_id}\n"
        f"📝 **ᴜsᴇʀ ɴᴀᴍᴇ :** {formatted_username}\n\n"
        f"💰 **ᴡɪᴛʜ疊ʀᴀᴡ ʙᴀʟᴀɴᴄᴇ ɪɴ ᴜsᴅᴛ :** ${balance:.2f}\n\n"
        f"⏰ **ᴛɪᴍᴇ & ᴅᴀᴛᴇ :** {get_bd_time()}\n\n"
        f"{countries_breakdown}"
    )
    return report

def create_zip_in_memory(files_dict: dict):
    """Creates a zip file in memory for instant session downloads."""
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in files_dict.items():
            zf.writestr(filename, data)
    mem_zip.seek(0)
    return mem_zip

def load_base_devices():
    """Loads base device structure from devices.json if available."""
    devices_path = os.path.join("utils", "devices.json")
    if os.path.exists(devices_path):
        with open(devices_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_dynamic_device_profile(platform_type="android"):
    """Generates over 500+ realistic device spoofing profiles to mimic real mobile devices."""
    base_data = load_base_devices()
    
    android_models = [
        "Samsung Galaxy S23 Ultra", "Samsung Galaxy S22", "Samsung A54 5G", "Samsung Z Fold 5",
        "Google Pixel 8 Pro", "Google Pixel 7a", "Xiaomi 13T Pro", "Xiaomi Redmi Note 12",
        "OnePlus 11", "OnePlus Nord 3", "Realme GT Neo 5", "Vivo X90 Pro", "OPPO Find X6",
        "Motorola Edge 40", "Nothing Phone 2", "Infinix Zero 30"
    ]
    android_sdks = ["Android 10", "Android 11", "Android 12", "Android 13", "Android 14"]
    app_versions = ["10.1.0", "10.2.2", "10.3.1", "10.4.0", "10.5.2", "10.6.0"]
    
    ios_models = ["iPhone 13 Mini", "iPhone 13 Pro", "iPhone 14", "iPhone 14 Plus", "iPhone 15", "iPhone 15 Pro Max"]
    ios_sdks = ["iOS 15.2", "iOS 16.0", "iOS 16.6", "iOS 17.0", "iOS 17.2"]
    
    platform = platform_type.lower()
    
    if platform == "android":
        model = random.choice(android_models)
        sdk = random.choice(android_sdks)
        app_ver = random.choice(app_versions)
        base = random.choice(base_data.get("android", [{"app_id": 2040, "app_hash": "b18441a1ed607e10e3949b218311a870"}]))
        
        return {
            "app_id": base["app_id"],
            "app_hash": base["app_hash"],
            "sdk": sdk,
            "device": model,
            "app_version": app_ver,
            "lang_code": "en"
        }
        
    elif platform in ["iphone", "ios"]:
        model = random.choice(ios_models)
        sdk = random.choice(ios_sdks)
        app_ver = random.choice(app_versions)
        base = random.choice(base_data.get("iphone", [{"app_id": 8, "app_hash": "7245de8e747a0d6fbe11f7e01494db81"}]))
        
        return {
            "app_id": base["app_id"],
            "app_hash": base["app_hash"],
            "sdk": sdk,
            "device": model,
            "app_version": app_ver,
            "lang_code": "en"
        }
        
    elif platform in ["win", "windows"]:
        win_versions = ["Windows 10 x64", "Windows 11 x64", "Windows 10 Pro"]
        base = random.choice(base_data.get("win", [{"app_id": 173491, "app_hash": "371e3be14114ca5822e032121c00222a"}]))
        
        return {
            "app_id": base["app_id"],
            "app_hash": base["app_hash"],
            "sdk": random.choice(win_versions),
            "device": "PC 64bit",
            "app_version": "4.12.2",
            "lang_code": "en"
        }
        
    else: # macOS
        mac_sdks = ["macOS 13.4", "macOS 14.1", "macOS 14.2"]
        mac_models = ["MacBook Air M1", "MacBook Pro M2", "iMac 24"]
        base = random.choice(base_data.get("mac", [{"app_id": 2834, "app_hash": "688f449512b3c10e98031d2793132717"}]))
        
        return {
            "app_id": base["app_id"],
            "app_hash": base["app_hash"],
            "sdk": random.choice(mac_sdks),
            "device": random.choice(mac_models),
            "app_version": "10.2.0",
            "lang_code": "en"
        }
