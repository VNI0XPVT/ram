import logging
from AnonMusic import app
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, ChatMemberUpdated

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.on_chat_member_updated()
async def handle_member_update(client: Client, update: ChatMemberUpdated):
    try:
        user = update.from_user
        chat = update.chat
        old = update.old_chat_member
        new = update.new_chat_member

        if not old or not new:
            return

        if old.status != new.status:
            pass
    except Exception as e:
        logger.error(f"🚫 [handle_member_update] Error: {e}")


@app.on_message(filters.video_chat_started)
async def video_chat_started_handler(client: Client, message: Message):
    try:
        pass
    except Exception as e:
        logger.error(f"🚫 [video_chat_started_handler] Error: {e}")


@app.on_message(filters.video_chat_ended)
async def video_chat_ended_handler(client: Client, message: Message):
    try:
        pass
    except Exception as e:
        logger.error(f"🚫 [video_chat_ended_handler] Error: {e}")


@app.on_message(filters.pinned_message)
async def pinned_message_handler(client: Client, message: Message):
    try:
        pinned = message.pinned_message
    except Exception as e:
        logger.error(f"🚫 [pinned_message_handler] Error: {e}")
