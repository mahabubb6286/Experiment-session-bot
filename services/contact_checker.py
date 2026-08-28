import logging
from pyrogram import Client
from pyrogram.raw.functions.contacts import ImportContacts
from pyrogram.raw.types import InputPhoneContact

logger = logging.getLogger(__name__)

async def verify_contact_restriction(client: Client) -> bool:
    """
    Verifies if account can perform contact sync/add action.
    Returns True if valid, False if restricted.
    """
    try:
        test_contact = InputPhoneContact(
            client_id=0,
            phone="+12025550143",
            first_name="Test",
            last_name="Verification"
        )
        await client.invoke(ImportContacts(contacts=[test_contact]))
        return True
    except Exception as e:
        logger.warning(f"Contact restriction check flagged: {e}")
        return False
