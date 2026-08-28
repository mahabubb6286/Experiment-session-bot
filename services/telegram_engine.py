import asyncio
import logging
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid
from utils.helpers import generate_dynamic_device_profile
from services.proxy_manager import get_proxy_dict
from services.spambot_checker import check_account_spambot_status
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

    async def process_account_login(self, code: str, user_id: int):
        config = await get_system_config()
        custom_2fa_password = config.get("two_fa_password", "Experiment247*")
        
        try:
            await self.client.sign_in(self.phone_number, self.phone_code_hash, code)
        except SessionPasswordNeeded:
            await self.client.check_password(custom_2fa_password)

        # SMART SPAMBOT CHECK
        spam_status = await check_account_spambot_status(self.client)
        
        # IF PERMANENT SPAM -> DO NOT SET 2FA, DISCONNECT AND REJECT
        if spam_status == "permanent_spam":
            await self.client.disconnect()
            reject_msg = (
                f"❗️ Account `{self.phone_number}` is permanent report, Robots won't accept it, Just accepts Free - New\n\n"
                f"👉 Use this robot to check your account for spam\n\n"
                f"@SpamBot\n"
                f"@SpamBot\n\n"
                f"⚠️ Robots will never accept this account"
            )
            return {"status": "rejected", "reason": "permanent_spam", "message": reject_msg}

        # IF FROZEN / BLOCKED -> REJECT
        elif spam_status == "frozen":
            await self.client.disconnect()
            reject_msg = f"❄️ Account `{self.phone_number}` is Frozen/Terminated by Telegram. Robots won't accept it."
            return {"status": "rejected", "reason": "frozen", "message": reject_msg}

        # ACCEPTED ACCOUNT (Free or New) -> SET 2FA & GENERATE SESSION
        if config.get("two_fa_add") and custom_2fa_password:
            try:
                await self.client.enable_cloud_password(custom_2fa_password)
            except Exception as e:
                logger.warning(f"Could not update 2FA Password: {e}")

        string_session = await self.client.export_session_string()
        await self.client.disconnect()
        
        return {
            "status": "success",
            "account_type": spam_status, # 'free' or 'new'
            "session_str": string_session
        }
