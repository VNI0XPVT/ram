import time
import re
import random
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import ChannelPrivate, SlowmodeWait, PeerIdInvalid, UserNotParticipant, ChatAdminRequired, FloodWait
from youtubesearchpython.__future__ import VideosSearch

import config
from AnonMusic import app
from AnonMusic.misc import _boot_
from AnonMusic.plugins.sudo.sudoers import sudoers_list
from AnonMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    blacklist_chat,
)
from AnonMusic.utils.decorators.language import LanguageStart
from AnonMusic.utils.formatters import get_readable_time
from AnonMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, LOGGER_ID
from strings import get_string


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            # Removed animation
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                has_spoiler=True,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                try:
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                    )
                except Exception as e:
                    print(f"Error sending log to LOGGER_ID: {e}")
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            
            try:
                results = VideosSearch(query, limit=1)
                search_result = (await results.next())["result"]
                if not search_result:
                    await m.edit_text(_["start_7"]) # Assuming you have a string for "No results found"
                    return
                
                result = search_result[0]
                title = result.get("title", "N/A")
                duration = result.get("duration", "N/A")
                views = result.get("viewCount", {}).get("short", "N/A")
                thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
                channellink = result.get("channel", {}).get("link", "N/A")
                channel = result.get("channel", {}).get("name", "N/A")
                link = result.get("link", "N/A")
                published = result.get("publishedTime", "N/A")
                
                searched_text = _["start_6"].format(
                    title, duration, views, published, channellink, channel, app.mention
                )
                key = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=_["S_B_8"], url=link),
                            InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                        ],
                    ]
                )
                await m.delete()
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    has_spoiler=True,
                    caption=searched_text,
                    reply_markup=key,
                )
                if await is_on_off(2):
                    try:
                        await app.send_message(
                            chat_id=config.LOGGER_ID,
                            text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                        )
                    except Exception as e:
                        print(f"Error sending log to LOGGER_ID: {e}")
            except Exception as e:
                await m.edit_text(_["error_message"].format(e)) # Generic error message
                print(f"Error in info section: {e}")
    else:
        out = private_panel(_)
        # Removed animation
        await message.reply_photo(
            photo=config.START_IMG_URL,
            has_spoiler=True,
            caption=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(out),
        )
        if await is_on_off(2):
            try:
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            except Exception as e:
                print(f"Error sending log to LOGGER_ID: {e}")


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    try:
        await message.reply_photo(
            photo=config.START_IMG_URL,
            has_spoiler=True,
            caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=InlineKeyboardMarkup(out),
        )
        await add_served_chat(message.chat.id)
    except ChannelPrivate:
        # Bot is not an admin or cannot send messages in this channel type
        print(f"Cannot send message in private channel: {message.chat.id}")
        return
    except SlowmodeWait as e:
        print(f"Slowmode active in chat {message.chat.id}. Waiting for {e.value} seconds.")
        await asyncio.sleep(e.value)
        try:
            await message.reply_photo(
                photo=config.START_IMG_URL,
                has_spoiler=True,
                caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=InlineKeyboardMarkup(out),
            )
            await add_served_chat(message.chat.id)
        except Exception as retry_e:
            print(f"Error after slowmode wait in chat {message.chat.id}: {retry_e}")
    except (ChatAdminRequired, UserNotParticipant) as e:
        print(f"Bot lacks permissions or is not a participant in chat {message.chat.id}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in start_gp for chat {message.chat.id}: {e}")


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                    print(f"Banned user {member.id} from chat {message.chat.id} as they are globally banned.")
                except ChatAdminRequired:
                    print(f"Bot is not admin to ban user {member.id} in chat {message.chat.id}.")
                except Exception as e:
                    print(f"Error banning user {member.id} in chat {message.chat.id}: {e}")
            
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    print(f"Leaving chat {message.chat.id} because it's not a supergroup.")
                    return await app.leave_chat(message.chat.id)
                
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    print(f"Leaving chat {message.chat.id} as it is blacklisted.")
                    return await app.leave_chat(message.chat.id)
                
                try:
                    ch = await app.get_chat(message.chat.id)
                    # Check for Myanmar characters in title or description
                    if (ch.title and re.search(r'[\u1000-\u109F]', ch.title)) or \
                       (ch.description and re.search(r'[\u1000-\u109F]', ch.description)):
                        await blacklist_chat(message.chat.id)
                        await message.reply_text("This group is not allowed to play songs due to detected unsupported characters.")
                        await app.send_message(LOGGER_ID, f"This group has been blacklisted automatically due to Myanmar characters in the chat title or description.\nTitle: {ch.title}\nID: {message.chat.id}")
                        print(f"Blacklisted and leaving chat {message.chat.id} due to Myanmar characters.")
                        return await app.leave_chat(message.chat.id)

                except PeerIdInvalid:
                    print(f"Could not get chat info for {message.chat.id}: PeerIdInvalid. Possibly bot was removed before getting chat details.")
                    # Continue without blacklisting if chat info can't be retrieved
                except Exception as e:
                    print(f"Error checking chat title/description for Myanmar characters in chat {message.chat.id}: {e}")
                    # Log and continue, don't stop the flow for this specific check
                    
                out = start_panel(_)
                await message.reply_photo(
                    photo=config.START_IMG_URL,
                    has_spoiler=True,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except FloodWait as e:
            print(f"FloodWait encountered in welcome for chat {message.chat.id}. Waiting for {e.value} seconds.")
            await asyncio.sleep(e.value)
            # You might want to retry the operation here or just log and move on.
            # For simplicity, I'm just logging and letting it pass.
        except Exception as ex:
            print(f"An unexpected error occurred in welcome for chat {message.chat.id} and user {member.id}: {ex}")
            # Optionally send a log to LOGGER_ID here for critical errors
            try:
                await app.send_message(LOGGER_ID, f"Error in welcome handler for chat {message.chat.id}: {ex}")
            except Exception as log_e:
                print(f"Could not send error log to LOGGER_ID: {log_e}")
