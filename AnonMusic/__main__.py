import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AnonMusic import LOGGER, app, userbot
from AnonMusic.core.call import Anony
from AnonMusic.misc import sudo
from AnonMusic.plugins import ALL_MODULES
from AnonMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS, COOKIES_URL
from AnonMusic.plugins.sudo.cookies import set_cookies

async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("⚙️ Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("AnonMusic.plugins" + all_module)
    LOGGER("AnonMusic.plugins").info("🗃️ Successfully Imported Modules...")
    await userbot.start()
    await Anony.start()
    try:
        await Anony.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("AnonMusic").error(
            "[×] Please turn on the videochat of your log group\channel Stopping Bot..."
        )
        exit()
    except:
        pass

    res = await set_cookies(COOKIES_URL)
    LOGGER("AnonMusic").info(f"{res}")
    await Anony.decorators()
    await idle()
    await app.stop()
    LOGGER("AnonMusic").info("🚫 Stopping AnonX Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
