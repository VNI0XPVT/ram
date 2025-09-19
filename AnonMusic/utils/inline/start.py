import config
from AnonMusic import app
from pyrogram.types import InlineKeyboardButton, WebAppInfo

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true",)
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], user_id=config.OWNER_ID),
            InlineKeyboardButton(text=_["S_B_5"], url=config.SUPPORT_CHANNEL),
        ],
        [
            InlineKeyboardButton(text="ʙᴏᴛ ᴅᴏᴄs", web_app=WebAppInfo(url=config.BOT_DOCS)),
            InlineKeyboardButton(text="ᴍɪɴɪ ᴀᴘᴘ", web_app=WebAppInfo(url=config.MINI_APP)),
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper"),
        ],
    
    ]
    
    return buttons
