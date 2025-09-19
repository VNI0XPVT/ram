import asyncio
import time

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import CallbackQuery, Message

from AnonMusic import app
from AnonMusic.core.call import Anony
from AnonMusic.misc import db
from AnonMusic.utils.database import get_assistant, get_authuser_names, get_cmode
from AnonMusic.utils.decorators import ActualAdminCB, AdminActual, language
from AnonMusic.utils.formatters import alpha_to_int, get_readable_time
from config import BANNED_USERS, adminlist, lyrical

rel = {}

@app.on_message(
    filters.command(["admincache", "reload", "refresh"]) & filters.group & ~BANNED_USERS
)
@language
async def reload_admin_cache(client, message: Message, _):
    try:
        now_time = time.time()
        if message.chat.id in rel and rel[message.chat.id] > now_time:
            left = get_readable_time(int(rel[message.chat.id] - now_time))
            return await message.reply_text(_["reload_1"].format(left))

        adminlist[message.chat.id] = []
        async for user in app.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        ):
            if user.privileges and user.privileges.can_manage_video_chats:
                adminlist[message.chat.id].append(user.user.id)

        authusers = await get_authuser_names(message.chat.id)
        for user in authusers:
            user_id = await alpha_to_int(user)
            adminlist[message.chat.id].append(user_id)

        rel[message.chat.id] = int(now_time) + 180
        await message.reply_text(_["reload_2"])

    except Exception as e:
        await message.reply_text(_["reload_3"])
        print(f"[ERROR - reload_admin_cache] {e}")


@app.on_message(filters.command(["reboot"]) & filters.group & ~BANNED_USERS)
@AdminActual
async def restartbot(client, message: Message, _):
    mystic = await message.reply_text(_["reload_4"].format(app.mention))
    await asyncio.sleep(1)

    try:
        db[message.chat.id] = []
        await Anony.stop_stream_force(message.chat.id)
    except Exception as e:
        print(f"[WARN - reboot] Stream stop failed in main chat: {e}")

    try:
        userbot = await get_assistant(message.chat.id)
        peer = message.chat.username or message.chat.id
        await userbot.resolve_peer(peer)
    except Exception as e:
        print(f"[WARN - reboot] Assistant resolve_peer failed in main chat: {e}")

    chat_id = await get_cmode(message.chat.id)
    if chat_id:
        try:
            got = await app.get_chat(chat_id)
            userbot = await get_assistant(chat_id)
            peer = got.username or chat_id
            await userbot.resolve_peer(peer)
            db[chat_id] = []
            await Anony.stop_stream_force(chat_id)
        except Exception as e:
            print(f"[WARN - reboot] Stream stop failed in cmode chat: {e}")

    return await mystic.edit_text(_["reload_5"].format(app.mention))


@app.on_callback_query(filters.regex("close") & ~BANNED_USERS)
async def close_menu(_, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        closed_msg = await callback_query.message.reply_text(
            f"🗑️ ᴄʟᴏsᴇᴅ ʙʏ : {callback_query.from_user.mention}"
        )
        await callback_query.message.delete()
        await asyncio.sleep(2)
        await closed_msg.delete()
    except Exception as e:
        print(f"[ERROR - close_menu] {e}")


@app.on_callback_query(filters.regex("stop_downloading") & ~BANNED_USERS)
@ActualAdminCB
async def stop_download(client, callback_query: CallbackQuery, _):
    message_id = callback_query.message.id
    task = lyrical.get(message_id)

    if not task:
        return await callback_query.answer(_["tg_4"], show_alert=True)

    if task.done() or task.cancelled():
        return await callback_query.answer(_["tg_5"], show_alert=True)

    try:
        task.cancel()
        lyrical.pop(message_id, None)
        await callback_query.answer(_["tg_6"], show_alert=True)
        return await callback_query.edit_message_text(
            _["tg_7"].format(callback_query.from_user.mention)
        )
    except Exception as e:
        print(f"[ERROR - stop_download] {e}")
        return await callback_query.answer(_["tg_8"], show_alert=True)
