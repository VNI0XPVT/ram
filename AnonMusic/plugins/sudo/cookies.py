from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton as Button
from AnonMusic import app
from config import COOKIES_URL, OWNER_ID
import asyncio
import os
import requests

# ✅ This function is now top-level and importable
async def set_cookies(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        cookies_dir = os.path.join(os.getcwd(), "cookies")
        os.makedirs(cookies_dir, exist_ok=True)

        cookies_path = os.path.join(cookies_dir, "cookies.txt")
        with open(cookies_path, "wb") as file:
            file.write(response.content)

        return f"✅ Bot cookies updated and saved to:\n<code>{cookies_path}</code>"

    except requests.exceptions.RequestException as e:
        return f"❌ Error downloading cookies:\n<code>{str(e)}</code>"
    except Exception as e:
        return f"❌ Unknown error:\n<code>{str(e)}</code>"

@app.on_message(
    filters.command(["updatecookies", "updatecookie", "getc"]) & filters.user(OWNER_ID)
)
async def update_cookies(client, message: Message):
    # Check if a URL is provided with the command
    if len(message.command) > 1:
        url = message.command[1]
        if not (
            url.startswith("https://gist.github.com/")
            or url.startswith("https://batbin.me/")
            or url.startswith("https://pastebin.com/")
        ):
            return await message.reply_text(
                "❌ Invalid cookies URL.\nOnly Gist, Pastebin, and Batbin links are supported.",
                reply_markup=InlineKeyboardMarkup([
                    [Button("❌ Close", callback_data="close_cb")]
                ])
            )
    else:
        url = COOKIES_URL

    res = await set_cookies(url)
    await message.reply_text(
        res,
        reply_markup=InlineKeyboardMarkup([
            [Button("ᴄʟᴏsᴇ", callback_data="close")]
        ])
    )
