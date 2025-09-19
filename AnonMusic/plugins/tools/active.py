from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from unidecode import unidecode

from AnonMusic import app
from AnonMusic.misc import SUDOERS
from AnonMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)

CLOSE_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
)

# 🔊 Active Voice Chats
@app.on_message(filters.command(["activevc", "vc", "activevoice"]) & SUDOERS)
async def activevc(_, message: Message):
    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ʟɪsᴛ...")
    served_chats = await get_active_chats()
    text = ""
    count = 0
    for x in served_chats:
        try:
            chat = await app.get_chat(x)
            title = unidecode(chat.title).upper()
            username = f"<a href=https://t.me/{chat.username}>{title}</a>" if chat.username else title
            text += f"<b>{count + 1}.</b> {username} [<code>{x}</code>]\n"
            count += 1
        except:
            await remove_active_chat(x)
            continue

    if not text:
        await mystic.edit_text("» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ғᴏᴜɴᴅ.", reply_markup=CLOSE_BUTTON)
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs :</b>\n\n{text}",
            reply_markup=CLOSE_BUTTON,
            disable_web_page_preview=True,
        )


# 📹 Active Video Chats
@app.on_message(filters.command(["activev", "av", "activevideo"]) & SUDOERS)
async def activevi_(_, message: Message):
    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ʟɪsᴛ...")
    served_chats = await get_active_video_chats()
    text = ""
    count = 0
    for x in served_chats:
        try:
            chat = await app.get_chat(x)
            title = unidecode(chat.title).upper()
            username = f"<a href=https://t.me/{chat.username}>{title}</a>" if chat.username else title
            text += f"<b>{count + 1}.</b> {username} [<code>{x}</code>]\n"
            count += 1
        except:
            await remove_active_video_chat(x)
            continue

    if not text:
        await mystic.edit_text("» No active video chats found.", reply_markup=CLOSE_BUTTON)
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs :</b>\n\n{text}",
            reply_markup=CLOSE_BUTTON,
            disable_web_page_preview=True,
        )


# 🔁 Combined Active Calls (/ac)
@app.on_message(filters.command(["ac", "activecalls"]) & SUDOERS)
async def active_calls_combined(_, message: Message):
    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴄᴀʟʟs (ᴠᴏɪᴄᴇ + ᴠɪᴅᴇᴏ)...")

    # Voice Chats
    voice_chats = await get_active_chats()
    voice_text, v_count = "", 0
    for x in voice_chats:
        try:
            chat = await app.get_chat(x)
            title = unidecode(chat.title).upper()
            username = f"<a href=https://t.me/{chat.username}>{title}</a>" if chat.username else title
            voice_text += f"<b>{v_count + 1}.</b> {username} [<code>{x}</code>]\n"
            v_count += 1
        except:
            await remove_active_chat(x)
            continue

    # Video Chats
    video_chats = await get_active_video_chats()
    video_text, vi_count = "", 0
    for x in video_chats:
        try:
            chat = await app.get_chat(x)
            title = unidecode(chat.title).upper()
            username = f"<a href=https://t.me/{chat.username}>{title}</a>" if chat.username else title
            video_text += f"<b>{vi_count + 1}.</b> {username} [<code>{x}</code>]\n"
            vi_count += 1
        except:
            await remove_active_video_chat(x)
            continue

    if not voice_text and not video_text:
        await mystic.edit_text("» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴏʀ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ғᴏᴜɴᴅ.", reply_markup=CLOSE_BUTTON)
        return

    final_text = "<b>🎙 ᴀᴄғᴏᴜɴᴅᴠᴏɪᴄᴇ ᴄʜᴀᴛs :</b>\n\n"
    final_text += voice_text if voice_text else "• ɴᴏɴᴇ\n"
    final_text += "\n<b>🎥 ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs :</b>\n\n"
    final_text += video_text if video_text else "• ɴᴏɴᴇ\n"

    await mystic.edit_text(
        final_text,
        reply_markup=CLOSE_BUTTON,
        disable_web_page_preview=True
    )
