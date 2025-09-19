import random
from typing import Union

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message
from pyrogram.errors import (
    MessageNotModified,
    MessageTooLong,
    RPCError, # Generic Pyrogram RPC error
    BadRequest, # General client-side error
)

from AnonMusic import app
from AnonMusic.utils import help_pannel
from AnonMusic.utils.database import get_lang
from AnonMusic.utils.decorators.language import LanguageStart, languageCB
from AnonMusic.utils.inline.help import help_back_markup, private_help_panel
import config
from strings import get_string, helpers


@app.on_message(filters.command(["help"]) & filters.private & ~config.BANNED_USERS)
@app.on_callback_query(filters.regex("settings_back_helper") & ~config.BANNED_USERS)
async def helper_private(
    client, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    
    chat_id = update.message.chat.id if is_callback else update.chat.id
    language = await get_lang(chat_id)
    _ = get_string(language)
    keyboard = help_pannel(_, True if is_callback else False)

    if is_callback:
        try:
            await update.answer() # Acknowledge the callback query
        except RPCError as e:
            print(f"Error answering callback query: {e}")
            # Continue execution even if answer fails

        try:
            await update.edit_message_text(
                _["help_1"].format(config.SUPPORT_CHAT), reply_markup=keyboard
            )
        except MessageNotModified:
            pass
        except MessageTooLong:
            await update.message.reply_text(
                _["help_1"].format(config.SUPPORT_CHAT), reply_markup=keyboard
            )
            print(f"MessageTooLong error when editing help message in chat {chat_id}")
        except RPCError as e:
            print(f"Error editing message for help_private callback in chat {chat_id}: {e}")
            # Fallback to sending a new message if edit fails
            try:
                await update.message.reply_photo(
                    photo=config.START_IMG_URL,
                    has_spoiler=True,
                    caption=_["help_1"].format(config.SUPPORT_CHAT),
                    reply_markup=keyboard,
                )
            except RPCError as e_fallback:
                print(f"Fallback photo send failed in chat {chat_id}: {e_fallback}")
                await update.message.reply_text("An error occurred while fetching help. Please try again.")

    else:
        try:
            pass 
        except RPCError as e:
            print(f"Error deleting command message in chat {update.chat.id}: {e}")
            
        try:
            await update.reply_photo(
                photo=config.START_IMG_URL,
                has_spoiler=True,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        except RPCError as e:
            print(f"Error sending help photo in chat {update.chat.id}: {e}")
            try:
                await update.reply_text(
                    _["help_1"].format(config.SUPPORT_CHAT), reply_markup=keyboard
                )
            except RPCError as e_fallback:
                print(f"Fallback text send failed in chat {update.chat.id}: {e_fallback}")


@app.on_message(filters.command(["help"]) & filters.group & ~config.BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    try:
        await message.reply_text(_["help_2"], reply_markup=InlineKeyboardMarkup(keyboard))
    except RPCError as e:
        print(f"Error sending help message in group {message.chat.id}: {e}")


@app.on_callback_query(filters.regex("help_callback") & ~config.BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except RPCError as e:
        print(f"Error answering callback query: {e}")

    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)

    help_sections = {
        "hb1": helpers.HELP_1,
        "hb2": helpers.HELP_2,
        "hb3": helpers.HELP_3,
        "hb4": helpers.HELP_4,
        "hb5": helpers.HELP_5,
        "hb6": helpers.HELP_6,
        "hb7": helpers.HELP_7,
        "hb8": helpers.HELP_8,
        "hb9": helpers.HELP_9,
        "hb10": helpers.HELP_10,
        "hb11": helpers.HELP_11,
        "hb12": helpers.HELP_12,
    }

    text_to_send = help_sections.get(cb, "Help section not found.")

    try:
        await CallbackQuery.edit_message_text(text_to_send, reply_markup=keyboard)
    except MessageNotModified:
        pass
    except MessageTooLong:
        try:
            await CallbackQuery.edit_message_text("The requested help text is too long. Sending as a new message...", reply_markup=keyboard)
            await CallbackQuery.message.reply_text(text_to_send, reply_markup=keyboard)
        except RPCError as e:
            print(f"Error handling MessageTooLong in help_cb for chat {CallbackQuery.message.chat.id}: {e}")
            await CallbackQuery.message.reply_text("An error occurred while displaying the help text. It might be too long.", reply_markup=keyboard)
    except BadRequest as e:
        print(f"BadRequest error when editing message in help_cb for chat {CallbackQuery.message.chat.id}: {e}")
        try:
            await CallbackQuery.message.reply_text(text_to_send, reply_markup=keyboard)
        except RPCError as e_fallback:
            print(f"Fallback reply failed in help_cb for chat {CallbackQuery.message.chat.id}: {e_fallback}")
            await CallbackQuery.message.reply_text("An error occurred. Please try again or check permissions.")
    except RPCError as e:
        print(f"Error editing message for help_cb in chat {CallbackQuery.message.chat.id}: {e}")
        await CallbackQuery.message.reply_text("An unexpected error occurred while loading the help section. Please try again.")
