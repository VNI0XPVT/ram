from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified, FloodWait, RPCError
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from AnonMusic import app
from AnonMusic.utils.database import (
    add_nonadmin_chat,
    get_authuser,
    get_authuser_names,
    get_playmode,
    get_playtype,
    get_upvote_count,
    is_nonadmin_chat,
    is_skipmode,
    remove_nonadmin_chat,
    set_playmode,
    set_playtype,
    set_upvotes,
    skip_off,
    skip_on,
)
from AnonMusic.utils.decorators.admins import ActualAdminCB
from AnonMusic.utils.decorators.language import language, languageCB
from AnonMusic.utils.inline.settings import (
    auth_users_markup,
    playmode_users_markup,
    setting_markup,
    vote_mode_markup,
)
from AnonMusic.utils.inline.start import private_panel
from config import BANNED_USERS, OWNER_ID

# --- Helper function for safe callback answers ---
async def safe_callback_answer(callback_query: CallbackQuery, text: str, show_alert: bool = False):
    """Answers a callback query, handling potential FloodWait or other RPC errors."""
    try:
        await callback_query.answer(text, show_alert=show_alert)
    except FloodWait as e:
        # Log this, or implement a retry mechanism if necessary
        print(f"FloodWait while answering callback: {e}")
        await callback_query.answer("Please wait a moment before trying again.", show_alert=True)
    except RPCError as e:
        # Log other RPC errors
        print(f"RPCError while answering callback: {e}")
        # Optionally, provide a generic error message to the user
        await callback_query.answer("An unexpected error occurred. Please try again.", show_alert=True)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error while answering callback: {e}")

# --- Helper function for safe message edits ---
async def safe_edit_message_reply_markup(callback_query: CallbackQuery, reply_markup: InlineKeyboardMarkup):
    """Edits a message's reply markup, handling MessageNotModified and other errors."""
    try:
        await callback_query.edit_message_reply_markup(reply_markup=reply_markup)
    except MessageNotModified:
        # This is common and usually means no action is needed
        pass
    except FloodWait as e:
        print(f"FloodWait while editing message reply markup: {e}")
        # Potentially inform the user or log
    except RPCError as e:
        print(f"RPCError while editing message reply markup: {e}")
    except Exception as e:
        print(f"Unexpected error while editing message reply markup: {e}")

async def safe_edit_message_text(callback_query: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Edits a message's text, handling MessageNotModified and other errors."""
    try:
        if reply_markup:
            await callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await callback_query.edit_message_text(text)
    except MessageNotModified:
        pass
    except FloodWait as e:
        print(f"FloodWait while editing message text: {e}")
    except RPCError as e:
        print(f"RPCError while editing message text: {e}")
    except Exception as e:
        print(f"Unexpected error while editing message text: {e}")

### Settings Command Handles the `/settings` or `/setting` command in groups.
@app.on_message(
    filters.command(["settings", "setting"]) & filters.group & ~BANNED_USERS
)
@language
async def settings_mar(client, message: Message, _):
    buttons = setting_markup(_)
    try:
        await message.reply_text(
            _["setting_1"].format(app.mention, message.chat.id, message.chat.title),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except RPCError as e:
        print(f"Error sending settings message: {e}")
        await message.reply_text("Failed to display settings. Please try again later.")

### Settings Callback Query Handles the `settings_helper` callback query to display general settings.
@app.on_callback_query(filters.regex("settings_helper") & ~BANNED_USERS)
@languageCB
async def settings_cb(client, CallbackQuery: CallbackQuery, _):
    await safe_callback_answer(CallbackQuery, _["set_cb_5"])
    buttons = setting_markup(_)
    await safe_edit_message_text(
        CallbackQuery,
        _["setting_1"].format(
            app.mention,
            CallbackQuery.message.chat.id,
            CallbackQuery.message.chat.title,
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

### Settings Back Callback Query Handles the `settingsback_helper` callback to navigate back from settings.
@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_markup(client, CallbackQuery: CallbackQuery, _):
    await safe_callback_answer(CallbackQuery, "") # Answer immediately to remove loading state

    if CallbackQuery.message.chat.type == ChatType.PRIVATE:
        # Assuming OWNER_ID is always resolvable, if not, add try-except
        await app.resolve_peer(OWNER_ID)
        buttons = private_panel(_)
        await safe_edit_message_text(
            CallbackQuery,
            _["start_2"].format(CallbackQuery.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = setting_markup(_)
        await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

### Info/Answer Callback Queries Handles various informational callback queries (e.g., explaining settings).
@app.on_callback_query(
    filters.regex(
        pattern=r"^(SEARCHANSWER|PLAYMODEANSWER|PLAYTYPEANSWER|AUTHANSWER|ANSWERVOMODE|VOTEANSWER|PM|AU|VM)$"
    )
    & ~BANNED_USERS
)
@languageCB
async def without_Admin_rights(client, CallbackQuery: CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    chat_id = CallbackQuery.message.chat.id

    if command == "SEARCHANSWER":
        await safe_callback_answer(CallbackQuery, _["setting_2"], show_alert=True)
        return
    elif command == "PLAYMODEANSWER":
        await safe_callback_answer(CallbackQuery, _["setting_5"], show_alert=True)
        return
    elif command == "PLAYTYPEANSWER":
        await safe_callback_answer(CallbackQuery, _["setting_6"], show_alert=True)
        return
    elif command == "AUTHANSWER":
        await safe_callback_answer(CallbackQuery, _["setting_3"], show_alert=True)
        return
    elif command == "VOTEANSWER":
        await safe_callback_answer(CallbackQuery, _["setting_8"], show_alert=True)
        return
    elif command == "ANSWERVOMODE":
        current_upvote_count = await get_upvote_count(chat_id)
        await safe_callback_answer(CallbackQuery, _["setting_9"].format(current_upvote_count), show_alert=True)
        return

    buttons = None
    if command == "PM":
        await safe_callback_answer(CallbackQuery, _["set_cb_2"], show_alert=False)
        playmode = await get_playmode(chat_id)
        is_direct_playmode = (playmode == "Direct")
        is_group_non_admin = await is_nonadmin_chat(chat_id)
        playtype = await get_playtype(chat_id)
        is_playtype_admin = (playtype != "Everyone")
        buttons = playmode_users_markup(_, is_direct_playmode, not is_group_non_admin, is_playtype_admin)
    elif command == "AU":
        await safe_callback_answer(CallbackQuery, _["set_cb_1"], show_alert=False)
        is_group_non_admin = await is_nonadmin_chat(chat_id)
        buttons = auth_users_markup(_, not is_group_non_admin)
    elif command == "VM":
        skip_mode_enabled = await is_skipmode(chat_id)
        current_upvote_count = await get_upvote_count(chat_id)
        buttons = vote_mode_markup(_, current_upvote_count, skip_mode_enabled)

    if buttons:
        await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

### Upvote Count Adjustment Handles the `FERRARIUDTI` callback to adjust the upvote count for skipping.
@app.on_callback_query(filters.regex("FERRARIUDTI") & ~BANNED_USERS)
@ActualAdminCB
async def addition(client, CallbackQuery: CallbackQuery, _):
    chat_id = CallbackQuery.message.chat.id
    mode = CallbackQuery.data.split(None, 1)[1]

    if not await is_skipmode(chat_id):
        await safe_callback_answer(CallbackQuery, _["setting_10"], show_alert=True)
        return

    current_upvote_count = await get_upvote_count(chat_id)
    new_upvote_count = current_upvote_count

    if mode == "M": # Minus
        new_upvote_count -= 2
        if new_upvote_count < 2: # Minimum limit
            new_upvote_count = 2
            await safe_callback_answer(CallbackQuery, _["setting_11"], show_alert=True)
            # No return, allow update if it was just above 2
    else: # Plus
        new_upvote_count += 2
        if new_upvote_count > 15: # Maximum limit
            new_upvote_count = 15
            await safe_callback_answer(CallbackQuery, _["setting_12"], show_alert=True)
            # No return, allow update if it was just below 15

    if new_upvote_count != current_upvote_count:
        await set_upvotes(chat_id, new_upvote_count)

    buttons = vote_mode_markup(_, new_upvote_count, True)
    await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

### Play Mode and Play Type Changes Handles callback queries for changing play mode, channel mode, and play type.
@app.on_callback_query(
    filters.regex(pattern=r"^(MODECHANGE|CHANNELMODECHANGE|PLAYTYPECHANGE)$")
    & ~BANNED_USERS
)
@ActualAdminCB
async def playmode_ans(client, CallbackQuery: CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    chat_id = CallbackQuery.message.chat.id

    await safe_callback_answer(CallbackQuery, _["set_cb_3"], show_alert=False)

    is_direct_playmode = None
    is_group_non_admin = None
    is_playtype_admin = None

    if command == "CHANNELMODECHANGE":
        if await is_nonadmin_chat(chat_id):
            await remove_nonadmin_chat(chat_id)
            is_group_non_admin = False # Now admin is required
        else:
            await add_nonadmin_chat(chat_id)
            is_group_non_admin = True # Now non-admin can play

        playmode = await get_playmode(chat_id)
        is_direct_playmode = (playmode == "Direct")
        playtype = await get_playtype(chat_id)
        is_playtype_admin = (playtype != "Everyone")

    elif command == "MODECHANGE":
        playmode = await get_playmode(chat_id)
        if playmode == "Direct":
            await set_playmode(chat_id, "Inline")
            is_direct_playmode = False
        else:
            await set_playmode(chat_id, "Direct")
            is_direct_playmode = True

        is_group_non_admin = await is_nonadmin_chat(chat_id)
        playtype = await get_playtype(chat_id)
        is_playtype_admin = (playtype != "Everyone")

    elif command == "PLAYTYPECHANGE":
        playtype = await get_playtype(chat_id)
        if playtype == "Everyone":
            await set_playtype(chat_id, "Admin")
            is_playtype_admin = True
        else:
            await set_playtype(chat_id, "Everyone")
            is_playtype_admin = False

        playmode = await get_playmode(chat_id)
        is_direct_playmode = (playmode == "Direct")
        is_group_non_admin = await is_nonadmin_chat(chat_id)

    buttons = playmode_users_markup(_, is_direct_playmode, not is_group_non_admin, is_playtype_admin)
    await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

### Authorized Users Management Handles callback queries for managing authorized users.
@app.on_callback_query(filters.regex(pattern=r"^(AUTH|AUTHLIST)$") & ~BANNED_USERS)
@ActualAdminCB
async def authusers_mar(client, CallbackQuery: CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    chat_id = CallbackQuery.message.chat.id

    if command == "AUTHLIST":
        _authusers = await get_authuser_names(chat_id)
        if not _authusers:
            await safe_callback_answer(CallbackQuery, _["setting_4"], show_alert=True)
            return
        else:
            await safe_callback_answer(CallbackQuery, _["set_cb_4"], show_alert=False)

            # Optimizing initial message edit to avoid redundant updates
            await safe_edit_message_text(CallbackQuery, _["auth_6"])

            msg = _["auth_7"].format(CallbackQuery.message.chat.title)
            j = 0
            for note in _authusers:
                _note = await get_authuser(chat_id, note)
                user_id = _note.get("auth_user_id")
                admin_id = _note.get("admin_id")
                admin_name = _note.get("admin_name")

                if not user_id:
                    continue # Skip if user_id is missing, data integrity check

                try:
                    user = await app.get_users(user_id)
                    user_first_name = user.first_name
                    j += 1
                except Exception as e:
                    print(f"Error fetching user {user_id}: {e}")
                    user_first_name = "Unknown User" # Fallback
                    # Consider removing invalid user_id from database if consistently failing
                    continue

                msg += f"{j}➤ {user_first_name}[<code>{user_id}</code>]\n"
                msg += f"   {_['auth_8']} {admin_name}[<code>{admin_id}</code>]\n\n"

            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data=f"AU"),
                        InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"close"),
                    ]
                ]
            )
            await safe_edit_message_text(CallbackQuery, msg, reply_markup=upl)
            return

    # If command is AUTH
    await safe_callback_answer(CallbackQuery, _["set_cb_3"], show_alert=False)
    
    is_non_admin = await is_nonadmin_chat(chat_id)
    if not is_non_admin:
        await add_nonadmin_chat(chat_id)
        buttons = auth_users_markup(_)
    else:
        await remove_nonadmin_chat(chat_id)
        buttons = auth_users_markup(_, True)
    
    await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

### Vote Mode ChangebHandles the `VOMODECHANGE` callback to toggle vote skip mode.
@app.on_callback_query(filters.regex("VOMODECHANGE") & ~BANNED_USERS)
@ActualAdminCB
async def vote_change(client, CallbackQuery: CallbackQuery, _):
    chat_id = CallbackQuery.message.chat.id
    await safe_callback_answer(CallbackQuery, _["set_cb_3"], show_alert=False)

    mod = None # Represents the current state after toggle
    if await is_skipmode(chat_id):
        await skip_off(chat_id)
    else:
        mod = True # Skipped mode is now ON
        await skip_on(chat_id)
    
    current_upvote_count = await get_upvote_count(chat_id)
    buttons = vote_mode_markup(_, current_upvote_count, mod)

    await safe_edit_message_reply_markup(CallbackQuery, InlineKeyboardMarkup(buttons))

