import asyncio
import speedtest

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from AnonMusic import app
from AnonMusic.misc import SUDOERS
from AnonMusic.utils.decorators.language import language


def perform_speedtest():
    try:
        test = speedtest.Speedtest()
        test.get_best_server()
        test.download()
        test.upload()
        test.results.share()
        return test.results.dict()
    except Exception as e:
        return {"error": str(e)}


@app.on_message(filters.command(["speedtest", "spt"]) & SUDOERS)
@language
async def speedtest_function(client, message: Message, _):
    m = await message.reply_text(_["server_11"])
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, perform_speedtest)

    if "error" in result:
        await m.edit_text(
            f"❌ <b>Speedtest Failed:</b>\n<code>{result['error']}</code>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✖ Close", callback_data="close")]]
            ),
        )
        return

    output = _["server_15"].format(
        result["client"]["isp"],
        result["client"]["country"],
        result["server"]["name"],
        result["server"]["country"],
        result["server"]["cc"],
        result["server"]["sponsor"],
        result["server"]["latency"],
        result["ping"],
    )

    try:
        await m.delete()
        await message.reply_photo(
            photo=result["share"],
            caption=output,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✖ Close", callback_data="close")]]
            ),
        )
    except Exception as e:
        await m.edit_text(
            f"✅ Speedtest completed, but an error occurred while sending result.\n\n<code>{e}</code>"
        )
