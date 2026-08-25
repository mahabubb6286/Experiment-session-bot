import os
import random
import string
import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid
from config_engine import ConfigEngine

class TelegramEngine:
    def __init__(self):
        self.config = ConfigEngine()

    def _generate_2fa_password(self, length=12):
        """স্বয়ংক্রিয় শক্তিশালী ২FA পাসওয়ার্ড জেনারেটর"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    async def send_otp(self, phone_number: str):
        """১. ওটিপি পাঠানোর ফাংশন"""
        device = self.config.get_random_device()
        proxy = self.config.get_country_proxy(phone_number)
        
        # ইউনিক সেশন নেম
        session_name = f"temp_{phone_number.replace('+', '')}"
        
        client = Client(
            name=session_name,
            api_id=self.config.api_id,
            api_hash=self.config.api_hash,
            device_model=device["device_model"],
            system_version=device["system_version"],
            app_version=device["app_version"],
            lang_code=device["lang_code"],
            system_lang_code=device["system_lang_code"],
            proxy=proxy,
            in_memory=True # লোকাল ডিক্সে সরাসরি ফাইল না বানিয়ে মেমোরিতে প্রসেস করবে
        )
        
        await client.connect()
        sent_code = await client.send_code(phone_number)
        
        return {
            "client": client,
            "phone_hash": sent_code.phone_code_hash,
            "session_name": session_name
        }

    async def complete_login(self, client: Client, phone_number: str, phone_hash: str, otp_code: str):
        """২. ওটিপি ভেরিফাই, ২FA সেটআপ ও সেশন জেনারেট করার ফাংশন"""
        try:
            # OTP দিয়ে সাইন-ইন
            await client.sign_in(phone_number, phone_hash, otp_code)
        except SessionPasswordNeeded:
            # যদি আগে থেকেই ২FA সেট করা থাকে (ব্যতিক্রমী কেস)
            return {"status": "error", "message": "Account already has 2FA enabled!"}
        except PhoneCodeInvalid:
            return {"status": "error", "message": "Invalid OTP Code!"}

        # অটোমেটিক ২FA পাসওয়ার্ড জেনারেট ও সেট করা
        new_2fa_pass = self._generate_2fa_password()
        try:
            await client.enable_cloud_password(new_2fa_pass)
        except Exception as e:
            print(f"2FA Setup Warning: {e}")

        # ডাইনামিকলি সেশন স্ট্রিং নেওয়া
        session_string = await client.export_session_string()
        await client.disconnect()

        return {
            "status": "success",
            "session_string": session_string,
            "two_fa_password": new_2fa_pass
        }
