import os
import shutil
import zipfile
import asyncio
from pyrogram import Client

class ConverterEngine:
    def __init__(self, output_dir="generated_sessions"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def create_zip_package(self, session_string: str, api_id: int, api_hash: str, phone_number: str, two_fa_password: str):
        """
        Session String থেকে .session ফাইল ও 2FA পাসওয়ার্ডসহ ZIP প্যাকেজ তৈরি করবে
        """
        clean_phone = phone_number.replace("+", "").strip()
        user_folder = os.path.join(self.output_dir, clean_phone)
        
        # ফোল্ডার ডিলিট/তৈরি করা
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
        os.makedirs(user_folder)

        # ১. Save .session file
        session_file_path = os.path.join(user_folder, f"{clean_phone}.session")
        client = Client(
            name=session_file_path.replace(".session", ""),
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string
        )
        await client.connect()
        await client.disconnect()

        # ২. Save Session String & Account Info
        info_path = os.path.join(user_folder, "account_info.txt")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"Phone Number: {phone_number}\n")
            f.write(f"2FA Password: {two_fa_password}\n\n")
            f.write(f"Pyrogram Session String:\n{session_string}\n")

        # ৩. Zip Creation
        zip_path = os.path.join(self.output_dir, f"{clean_phone}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(user_folder):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_file_path, user_folder)
                    zipf.write(full_file_path, arcname)

        # ক্লিনআপ
        shutil.rmtree(user_folder)

        return zip_path
