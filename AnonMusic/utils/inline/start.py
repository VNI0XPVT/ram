def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], user_id=config.OWNER_ID),
            InlineKeyboardButton(text=_["S_B_5"], url=config.SUPPORT_CHANNEL or "https://t.me/YourSupportChannel"),
        ],
        [
            InlineKeyboardButton(
                text="ᴀᴠɪᴀᴛᴏʀ ʜᴀᴄᴋ",
                url=config.AVIATOR_HACK if getattr(config, "AVIATOR_HACK", None) else "https://t.me/Oliver_Income1"
            ),
            InlineKeyboardButton(
                text="ᴍɪɴɪ ᴀᴘᴘ",
                web_app=WebAppInfo(url=config.MINI_APP if getattr(config, "MINI_APP", None) else "https://example.com")
            ),
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_back_helper"),
        ],
    ]
    return buttons
