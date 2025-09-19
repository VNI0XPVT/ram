import asyncio
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import MessageDeleteForbidden, ChatAdminRequired # ये दो एक्सेप्शन्स जिन्हें हम हैंडल करेंगे

from AnonMusic.utils.database import get_assistant
from AnonMusic import YouTube, app
from AnonMusic.core.call import Anony
from AnonMusic.misc import SUDOERS, db
from AnonMusic.utils.database import (
    get_active_chats,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_music_playing,
    is_nonadmin_chat,
    music_off,
    music_on,
    set_loop,
)
from AnonMusic.utils.decorators.language import languageCB
from AnonMusic.utils.formatters import seconds_to_min
from AnonMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from AnonMusic.utils.thumbnails import get_thumb
from config import (
    BANNED_USERS,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    SUPPORT_CHAT,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
    autoclean,
)
from strings import get_string

checker = {}
upvoters = {}


@app.on_callback_query(filters.regex("unban_assistant"))
async def unban_assistant(_, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    userbot = await get_assistant(chat_id)
    
    try:
        await app.unban_chat_member(chat_id, userbot.id)
        await callback.answer(
            "❖ ᴍʏ ᴀssɪsᴛᴀɴᴛ ɪᴅ ᴜɴʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ\n\n"
            "● ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴘʟᴀʏ sᴏɴɢs\n\n"
            "● ᴛʜᴀɴᴋ ʏᴏᴜ ᴅᴀʀʟɪɴɢ", 
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            "❖ ғᴀɪʟᴇᴅ ᴛᴏ ᴜɴʙᴀɴ ᴍʏ ᴀssɪsᴛᴀɴᴛ ʙᴇᴄᴀᴜsᴇ ɪ ᴅᴏɴᴛ ʜᴀᴠᴇ ʙᴀɴ ᴘᴏᴡᴇʀ\n\n"
            "● ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴍᴇ ʙᴀɴ ᴘᴏᴡᴇʀ sᴏ ᴛʜᴀᴛ 𝖨 ᴄᴀɴ ᴜɴʙᴀɴ ᴍʏ ᴀssɪsᴛᴀɴᴛ ɪᴅ", 
            show_alert=True
        )


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery:CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention
    if command == "UpVote":
        if chat_id not in votemode:
            votemode[chat_id] = {}
        if chat_id not in upvoters:
            upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters:
            upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote:
            votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] += 1
        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])
        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.edit_message_text(f"फ़ेल हुआ।")
                await asyncio.sleep(5)
                try:
                    await msg.delete() # या CallbackQuery.message.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass # परमिशन न होने पर चुपचाप इग्नोर करें
                return
            try:
                if current["vidid"] != exists["vidid"]:
                    # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                    msg = await CallbackQuery.edit_message_text(_["admin_35"])
                    await asyncio.sleep(5)
                    try:
                        await msg.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass
                    return
                if current["file"] != exists["file"]:
                    # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                    msg = await CallbackQuery.edit_message_text(_["admin_35"])
                    await asyncio.sleep(5)
                    try:
                        await msg.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass
                    return
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.edit_message_text(_["admin_36"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            try:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
            except:
                pass
            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"
        else:
            if (
                CallbackQuery.from_user.id
                in upvoters[chat_id][CallbackQuery.message.id]
            ):
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"👍 {get_upvotes}",
                            callback_data=f"ADMIN  UpVote|{chat_id}_{counter}",
                        )
                    ]
                ]
            )
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
            msg = await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
            await asyncio.sleep(5)
            try:
                await msg.delete() # या CallbackQuery.message.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass
            return
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
                if not admins:
                    return await CallbackQuery.answer(_["admin_13"], show_alert=True)
                else:
                    if CallbackQuery.from_user.id not in admins:
                        return await CallbackQuery.answer(
                            _["admin_14"], show_alert=True
                        )
    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await Anony.pause_stream(chat_id)
        # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
        msg = await CallbackQuery.message.reply_text(
            _["admin_2"].format(mention), reply_markup=close_markup(_)
        )
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except (MessageDeleteForbidden, ChatAdminRequired):
            pass
    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await Anony.resume_stream(chat_id)
        # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
        msg = await CallbackQuery.message.reply_text(
            _["admin_4"].format(mention), reply_markup=close_markup(_)
        )
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except (MessageDeleteForbidden, ChatAdminRequired):
            pass
    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await Anony.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
        msg = await CallbackQuery.message.reply_text(
            _["admin_5"].format(mention), reply_markup=close_markup(_)
        )
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except (MessageDeleteForbidden, ChatAdminRequired):
            pass
        # Original message को डिलीट करें, परमिशन हैंडलिंग के साथ
        try:
            await CallbackQuery.message.delete()
        except (MessageDeleteForbidden, ChatAdminRequired):
            pass
    elif command == "Skip" or command == "Replay":
        check = db.get(chat_id)
        if command == "Skip":
            txt = f"⏮️ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ └ʙʏ : {mention}"
            popped = None
            try:
                popped = check.pop(0)
                if popped:
                    rem = popped["file"]
                    autoclean.remove(rem)
                if not check:
                    # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                    msg_edited = await CallbackQuery.edit_message_text(
                        f"⏮️ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ └ʙʏ : {mention}"
                    )
                    await asyncio.sleep(5)
                    try:
                        await msg_edited.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass

                    msg_reply = await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    await asyncio.sleep(5)
                    try:
                        await msg_reply.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass
                    try:
                        return await Anony.stop_stream(chat_id)
                    except:
                        return
            except:
                try:
                    # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                    msg_edited = await CallbackQuery.edit_message_text(
                        f"⏮️ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ └ʙʏ : {mention}"
                    )
                    await asyncio.sleep(5)
                    try:
                        await msg_edited.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass

                    msg_reply = await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    await asyncio.sleep(5)
                    try:
                        await msg_reply.delete()
                    except (MessageDeleteForbidden, ChatAdminRequired):
                        pass
                    return await Anony.stop_stream(chat_id)
                except:
                    return
        else:
            txt = f"🔁 sᴛʀᴇᴀᴍ ʀᴇ-ᴘʟᴀʏᴇᴅ └ʙʏ : {mention}"
        await CallbackQuery.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        user_id = check[0]["user_id"]
        duration = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.message.reply_text(
                    text=_["admin_7"].format(title),
                    reply_markup=close_markup(_),
                )
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Anony.skip_stream(chat_id, link, video=status, image=image)
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.message.reply_text(_["call_6"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            button = stream_markup(_, chat_id)
            img = await get_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
            msg = await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await asyncio.sleep(5)
            try:
                await msg.delete() # या CallbackQuery.message.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass
        elif "vid_" in queued:
            mystic = await CallbackQuery.message.reply_text(
                _["call_7"], disable_web_page_preview=True
            )
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=status,
                )
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await mystic.edit_text(_["call_6"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Anony.skip_stream(chat_id, file_path, video=status, image=image)
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await mystic.edit_text(_["call_6"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            button = stream_markup(_, chat_id)
            img = await get_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
            msg = await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await asyncio.sleep(5)
            try:
                await msg.delete() # या CallbackQuery.message.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass
            # mystic को तुरंत डिलीट करें, परमिशन हैंडलिंग के साथ
            try:
                await mystic.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass
        elif "index_" in queued:
            try:
                await Anony.skip_stream(chat_id, videoid, video=status)
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.message.reply_text(_["call_6"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            button = stream_markup(_, chat_id)
            run = await CallbackQuery.message.reply_photo(
                photo=STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
            msg = await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await asyncio.sleep(5)
            try:
                await msg.delete() # या CallbackQuery.message.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass
        else:
            if videoid == "telegram":
                image = None
            elif videoid == "soundcloud":
                image = None
            else:
                try:
                    image = await YouTube.thumbnail(videoid, True)
                except:
                    image = None
            try:
                await Anony.skip_stream(chat_id, queued, video=status, image=image)
            except:
                # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
                msg = await CallbackQuery.message.reply_text(_["call_6"])
                await asyncio.sleep(5)
                try:
                    await msg.delete()
                except (MessageDeleteForbidden, ChatAdminRequired):
                    pass
                return
            if videoid == "telegram":
                button = stream_markup(_, chat_id)
                run = await CallbackQuery.message.reply_photo(
                    photo=TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    caption=_["stream_1"].format(
                        SUPPORT_CHAT, title[:23], duration, user
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif videoid == "soundcloud":
                button = stream_markup(_, chat_id)
                run = await CallbackQuery.message.reply_photo(
                    photo=SOUNCLOUD_IMG_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    caption=_["stream_1"].format(
                        SUPPORT_CHAT, title[:23], duration, user
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                button = stream_markup(_, chat_id)
                img = await get_thumb(videoid)
                run = await CallbackQuery.message.reply_photo(
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        duration,
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            # 5 सेकंड बाद डिलीट करने के लिए, परमिशन हैंडलिंग के साथ:
            msg = await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await asyncio.sleep(5)
            try:
                await msg.delete() # या CallbackQuery.message.delete()
            except (MessageDeleteForbidden, ChatAdminRequired):
                pass


async def markup_timer():
    while not await asyncio.sleep(7):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration_seconds = int(playing[0]["seconds"])
                if duration_seconds == 0:
                    continue
                try:
                    mystic = playing[0]["mystic"]
                except:
                    continue
                try:
                    check = checker[chat_id][mystic.id]
                    if check is False:
                        continue
                except:
                    pass
                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except:
                    _ = get_string("en")
                try:
                    buttons = stream_markup_timer(
                        _,
                        chat_id,
                        seconds_to_min(playing[0]["played"]),
                        playing[0]["dur"],
                    )
                    await mystic.edit_reply_markup(
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                except:
                    continue
            except:
                continue


asyncio.create_task(markup_timer())
