from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Chat

import config
from ..logging import LOGGER


class Anony(Client):
    def __init__(self):
        LOGGER(__name__).info("🈵 Initializing bot client")
        super().__init__(
            name="AnonMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            self.id = me.id
            self.name = f"{me.first_name} {(me.last_name or '')}".strip()
            self.username = me.username
            self.mention = me.mention

            LOGGER(__name__).info(f"✅ Bot logged in as {self.name} (@{self.username})")

            # Try sending a startup message
            try:
                await self.send_message(
                    chat_id=config.LOGGER_ID,
                    text=(
                        f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                        f"🆔 ɪᴅ : <code>{self.id}</code>\n"
                        f"📛 ɴᴀᴍᴇ : {self.name}\n"
                        f"🔰 ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                    ),
                )
            except (errors.PeerIdInvalid, errors.ChannelInvalid) as e:
                LOGGER(__name__).error(
                    "❌ Cannot send log message. Make sure bot is added to the log group and has permission."
                )
                raise SystemExit(1)
            except Exception as e:
                LOGGER(__name__).error(
                    f"❌ Unexpected error while sending startup message: {type(e).__name__}: {e}"
                )
                raise SystemExit(1)

            # Check admin permission in log group
            try:
                member = await self.get_chat_member(config.LOGGER_ID, self.id)
                if member.status != ChatMemberStatus.ADMINISTRATOR:
                    LOGGER(__name__).error(
                        "❌ Please promote the bot as an admin in the log group."
                    )
                    raise SystemExit(1)
            except errors.ChatAdminRequired:
                LOGGER(__name__).error("❌ Bot lacks admin rights in the log group.")
                raise SystemExit(1)
            except Exception as e:
                LOGGER(__name__).error(
                    f"❌ Failed to check bot's admin status: {type(e).__name__}: {e}"
                )
                raise SystemExit(1)

            LOGGER(__name__).info("✅ Bot started successfully.")

        except Exception as e:
            LOGGER(__name__).exception(f"❌ Failed to start bot: {e}")
            raise SystemExit(1)

    async def stop(self):
        try:
            await super().stop()
            LOGGER(__name__).info("🛑 Bot stopped successfully.")
        except Exception as e:
            LOGGER(__name__).exception(f"❌ Error during shutdown: {e}")
