import asyncio
import logging
from datetime import datetime

from pyrogram.enums import ChatType

import config
from AnonMusic import app
from AnonMusic.core.call import Anony, autoend
from AnonMusic.utils.database import get_client, is_active_chat, is_autoend

logger = logging.getLogger(__name__)


async def auto_leave():
    """Auto leave inactive chats if enabled in config."""
    if not config.AUTO_LEAVING_ASSISTANT:
        return

    while True:
        await asyncio.sleep(config.ASSISTANT_LEAVE_TIME)
        from AnonMusic.core.userbot import assistants

        for num in assistants:
            client = await get_client(num)
            left_count = 0
            try:
                async for dialog in client.get_dialogs():
                    chat = dialog.chat
                    if chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL]:
                        continue

                    if chat.id in [
                        config.LOGGER_ID,
                        -1002500829755,
                        -1002204995394,
                    ]:
                        continue

                    if left_count >= 20:
                        break

                    if not await is_active_chat(chat.id):
                        try:
                            await client.leave_chat(chat.id)
                            left_count += 1
                            logger.info(f"Left inactive chat {chat.id}")
                        except Exception as e:
                            logger.warning(f"Failed to leave chat {chat.id}: {e}")
            except Exception as e:
                logger.error(f"Auto leave failed for assistant {num}: {e}")


async def auto_end():
    """Auto end inactive streams if enabled in config."""
    if not config.AUTO_END_STREAM:
        return

    while True:
        await asyncio.sleep(5)
        if not await is_autoend():
            continue

        for chat_id, timer in list(autoend.items()):
            if not timer:
                continue

            if datetime.now() > timer:
                if not await is_active_chat(chat_id):
                    autoend.pop(chat_id, None)
                    continue

                autoend.pop(chat_id, None)
                try:
                    await Anony.stop_stream(chat_id)
                    logger.info(f"Auto-ended stream in chat {chat_id}")
                except Exception as e:
                    logger.warning(f"Failed to stop stream in {chat_id}: {e}")

                try:
                    await app.send_message(
                        chat_id,
                        "🔇 Bot automatically ended the stream due to inactivity.",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send auto-end message in {chat_id}: {e}")


# Launch background tasks
if config.AUTO_LEAVING_ASSISTANT:
    asyncio.create_task(auto_leave())

if config.AUTO_END_STREAM:
    asyncio.create_task(auto_end())
