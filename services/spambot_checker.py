import asyncio
import logging
from pyrogram import Client

logger = logging.getLogger(__name__)

async def check_account_spambot_status(client: Client) -> str:
    """
    Smartly analyzes response from Telegram's official @SpamBot.
    Handles dynamic user names and multi-phrase matching for New Accounts.
    Returns: 'free', 'new', 'permanent_spam', 'frozen', or 'unknown'
    """
    try:
        bot_username = "SpamBot"
        await client.send_message(bot_username, "/start")
        await asyncio.sleep(3.0)  # Wait for SpamBot response
        
        messages = []
        async for msg in client.get_chat_history(bot_username, limit=1):
            if msg.text:
                messages.append(msg.text)
            
        if not messages:
            return "unknown"
            
        bot_reply = messages[0].strip()
        bot_reply_lower = bot_reply.lower()
        
        # 1. FREE ACCOUNT DETECT
        if "good news, no limits are currently applied to your account" in bot_reply_lower or "free as a bird" in bot_reply_lower:
            return "free"
            
        # 2. NEW ACCOUNT DETECT (Checked with both patterns for maximum accuracy)
        elif (
            "unfortunately, some phone numbers may trigger a harsh response from our anti-spam systems" in bot_reply_lower
            or "subscribe to telegram premium to get less strict limits" in bot_reply_lower
            or "submit a complaint to our moderators or subscribe to telegram premium" in bot_reply_lower
        ):
            return "new"
            
        # 3. FROZEN / TERMINATED ACCOUNT DETECT
        elif "blocked for violations of the telegram terms of service" in bot_reply_lower or "terms of service based on user reports" in bot_reply_lower:
            return "frozen"
            
        # 4. PERMANENT SPAM REPORT DETECT (Dynamic Name Handling)
        elif (
            "while the account is limited, you will not be able to send messages" in bot_reply_lower 
            or "i’m very sorry that you had to contact me" in bot_reply_lower
            or "i'm very sorry that you had to contact me" in bot_reply_lower
        ):
            return "permanent_spam"
            
        else:
            # Fallback Safety Check
            if "limited" in bot_reply_lower or "restricted" in bot_reply_lower:
                return "permanent_spam"
            return "free"
            
    except Exception as e:
        logger.error(f"SpamBot Smart Verification Error: {e}")
        return "unknown"
