import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, RPCError
from AnonMusic import app

@app.on_message(filters.command(["admins", "staff"]))
async def get_admins(client: Client, message: Message):
    try:
        admins = []
        owner = None

        async for member in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.privileges and not member.privileges.is_anonymous and not member.user.is_bot:
                if member.status == ChatMemberStatus.OWNER:
                    owner = member.user
                else:
                    admins.append(member.user)

        total = len(admins) + (1 if owner else 0)
        text = f"❖ ɢʀᴏᴜᴘ sᴛᴀғғ - {message.chat.title}\n\n"

        if owner:
            name = f"@{owner.username}" if owner.username else owner.mention
            text += f"❖ ᴏᴡɴᴇʀ\n└ {name}\n\n● ᴀᴅᴍɪɴs\n"
        else:
            text += "❖ ᴏᴡɴᴇʀ\n└ <i>Hidden</i>\n\n● ᴀᴅᴍɪɴs\n"

        if not admins:
            text += "└ <i>ᴀᴅᴍɪɴs ᴀʀᴇ ʜɪᴅᴅᴇɴ</i>"
        else:
            for i, admin in enumerate(admins):
                name = f"@{admin.username}" if admin.username else admin.mention
                if i == len(admins) - 1:
                    text += f"└ {name}\n\n"
                else:
                    text += f"├ {name}\n"

        text += f"❖ | **ᴛᴏᴛᴀʟ ɴᴜᴍʙᴇʀ ᴏғ ᴀᴅᴍɪɴs**: {total}"

        await message.reply(text)

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except RPCError as e:
        await message.reply(f"🚫 An error occurred: `{str(e)}`")
    except Exception as e:
        print(f"[ADMIN CMD ERROR] {e}")
        await message.reply("⚠️ Unexpected error while fetching admin list.")

@app.on_message(filters.command("bots"))
async def get_bots(client: Client, message: Message):
    try:
        bots = []
        async for bot in app.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.BOTS):
            bots.append(bot.user)

        total = len(bots)
        text = f"**❖ ʙᴏᴛ ʟɪsᴛ - {message.chat.title}**\n\n● ʙᴏᴛs\n"

        if not bots:
            text += "└ <i>No bots found in this chat.</i>"
        else:
            for i, bot in enumerate(bots):
                name = f"@{bot.username}" if bot.username else bot.mention
                if i == len(bots) - 1:
                    text += f"└ {name}\n\n"
                else:
                    text += f"├ {name}\n"
            text += f"❖ | **ᴛᴏᴛᴀʟ ɴᴜᴍʙᴇʀ ᴏғ ʙᴏᴛs**: {total}"

        await message.reply(text)

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except RPCError as e:
        await message.reply(f"🚫 An error occurred: `{str(e)}`")
    except Exception as e:
        print(f"[BOTS CMD ERROR] {e}")
        await message.reply("⚠️ Unexpected error while fetching bot list.")
