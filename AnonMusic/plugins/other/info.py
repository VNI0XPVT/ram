from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from AnonMusic import app


@app.on_message(filters.command('id'))
async def getid(client, message: Message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.id
    reply = message.reply_to_message

    text = f"<b>❖ <a href='{message.link}'>Message ID:</a></b> <code>{message_id}</code>\n"
    text += f"<b>❖ <a href='tg://user?id={your_id}'>Your ID:</a></b> <code>{your_id}</code>\n"

    if not message.command:
        message.command = message.text.split()

    if len(message.command) == 2:
        try:
            split = message.text.split(None, 1)[1].strip()
            user_id = (await client.get_users(split)).id
            text += f"<b>❖ <a href='tg://user?id={user_id}'>User ID:</a></b> <code>{user_id}</code>\n"
        except Exception:
            return await message.reply_text("This user doesn't exist.", quote=True)

    if chat.username:
        text += f"<b>❖ <a href='https://t.me/{chat.username}'>Chat ID:</a></b> <code>{chat.id}</code>\n\n"
    else:
        text += f"<b>❖ Chat ID:</b> <code>{chat.id}</code>\n\n"

    if (
        not getattr(reply, "empty", True)
        and not message.forward_from_chat
        and not reply.sender_chat
    ):
        text += f"<b>❖ <a href='{reply.link}'>Replied Message ID:</a></b> <code>{reply.id}</code>\n"
        text += f"<b>❖ <a href='tg://user?id={reply.from_user.id}'>Replied User ID:</a></b> <code>{reply.from_user.id}</code>\n\n"

    if reply and reply.forward_from_chat:
        text += f"<b>❖ Forwarded from channel:</b> {reply.forward_from_chat.title}, ID: <code>{reply.forward_from_chat.id}</code>\n\n"

    if reply and reply.sender_chat:
        text += f"<b>❖ Replied chat/channel ID:</b> <code>{reply.sender_chat.id}</code>"

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Close", callback_data="close")]]
    )

    await message.reply_text(
        text,
        reply_markup=markup,
        disable_web_page_preview=True
    )


@app.on_message(filters.command("info"))
async def get_user_info(client, message: Message):
    reply = message.reply_to_message
    user = None

    if reply:
        user = reply.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except:
            return await message.reply_text("🚫 Couldn't fetch user. Please check the username or ID.")
    else:
        user = message.from_user

    if not user:
        return await message.reply_text("🚫 User not found. Please try again.")

    text = (
        "<b>👤 User Information:</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Name:</b> {user.first_name}\n"
        f"{'🔗 <b>Username:</b> @' + user.username if user.username else '🔗 <b>Username:</b> None'}\n"
        f"🤖 <b>Bot:</b> {'Yes' if user.is_bot else 'No'}\n"
        f"🧷 <b>Mention:</b> {user.mention}"
    )

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{user.first_name}", user_id=user.id)]]
    )

    await message.reply_text(
        text,
        reply_markup=markup
    )
