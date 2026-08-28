import io
import zipfile
import phonenumbers
from phonenumbers import geocoder
from datetime import datetime
import pytz

def parse_phone_details(phone_number: str):
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
    bd_tz = pytz.timezone("Asia/Dhaka")
    now = datetime.now(bd_tz)
    return now.strftime("%m/%d/%y %H:%M:%S ( Bangladesh (UTC+6) )")

def format_withdraw_report(card_name: str, user_id: int, username: str, balance: float, countries_breakdown: str):
    formatted_user_id = f"`{user_id}`"
    formatted_username = f"@{username}" if username else "N/A"
    
    report = (
        f"🌳 **𝗡𝗲𝘄 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄 𝗙𝗿𝗼𝗺 {card_name}**\n\n"
        f"👤 **ᴜsᴇʀ ɪᴅ :** {formatted_user_id}\n"
        f"📝 **ᴜsᴇʀ ɴᴀᴍᴇ :** {formatted_username}\n\n"
        f"💰 **ᴡɪᴛʜᴅʀᴀᴡ ʙᴀʟᴀɴᴄᴇ ɪɴ ᴜsᴅᴛ :** ${balance:.2f}\n\n"
        f"⏰ **ᴛɪᴍᴇ & ᴅᴀᴛᴇ :** {get_bd_time()}\n\n"
        f"{countries_breakdown}"
    )
    return report

def create_zip_in_memory(files_dict: dict):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, data in files_dict.items():
            zf.writestr(filename, data)
    mem_zip.seek(0)
    return mem_zip
