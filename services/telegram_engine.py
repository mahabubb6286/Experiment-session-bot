import asyncio
import os
import logging
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid
from utils.helpers import generate_dynamic_device_profile
from services.proxy_manager import get_proxy_dict
from database.config_db import get_system_config

logger = logging.getLogger(__name__)

class TelegramEngine:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.client = None
        self.phone_code_hash = None
        
    async def initialize_client(self):
        config = await get_system_config()
        api_id = config.get("api_id")
        api_hash = config.get("api_hash")
        
        if not api_id or not api_hash:
            raise ValueError("API ID and API Hash are not configured in system settings!")
            
        # Get dynamic real device parameters
        device = generate_dynamic_device_profile("android")
        proxy = await get_proxy_dict()
        
        session_name = f"temp_{self.phone_number.replace('+', '')}"
        
        self.client = Client(
            name=session_name,
            api_id=int(api_id),
            api_hash=api_hash,
            device_model=device["device"],
            system_version=device["sdk"],
            app_version=device["app_version"],
            lang_code=device["lang_code"],
            proxy=proxy,
            in_memory=True
        )
        await self.client.connect()

    async def send_otp(self):
        await self.initialize_client()
        sent_code = await self.client.send_code(self.phone_number)
        self.phone_code_hash = sent_code.phone_code_hash
        return self.phone_code_hash

    async def complete_login(self, code: str, custom_2fa_password: str = None):
        try:
            await self.client.sign_in(self.phone_number, self.phone_code_hash, code)
        except SessionPasswordNeeded:
            if not custom_2fa_password:
                config = await get_system_config()
                custom_2fa_password = config.get("two_fa_password", "Experiment247*")
            await self.client.check_password(custom_2fa_password)
            
        # Set Admin Custom 2FA Password if enabled
        config = await get_system_config()
        if config.get("two_fa_add") and custom_2fa_password:
            try:
                await self.client.enable_cloud_password(custom_2fa_password)
            except Exception as e:
                logger.warning(f"Could not update 2FA Password: {e}")

        # Export String Session
        string_session = await self.client.export_session_string()
        await self.client.disconnect()
        return string_session
