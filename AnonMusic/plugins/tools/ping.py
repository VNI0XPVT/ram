from datetime import datetime
import asyncio # Import asyncio for better async error handling

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait # Import specific Pyrogram errors

from AnonMusic import app
from AnonMusic.core.call import Anony
from AnonMusic.utils import bot_sys_stats
from AnonMusic.utils.decorators.language import language
from AnonMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL

# Import logging if not already globally available in this file's context
# from AnonMusic.logging import LOGGER 


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    """
    Handles the /ping and /alive commands, providing bot status and performance metrics.
    """
    start_time = datetime.now()
    initial_response = None # Initialize to None

    try:
        # Send initial message with photo and placeholder text
        initial_response = await message.reply_photo(
            photo=PING_IMG_URL,
            caption=_["ping_1"].format(app.mention),
        )
    except FloodWait as e:
        # Handle FloodWait specific to sending the photo
        LOGGER(__name__).warning(f"FloodWait encountered when sending ping photo: {e.value} seconds. Skipping photo for this ping.")
        # If floodwait, try sending text message instead
        try:
            initial_response = await message.reply_text(_["ping_1"].format(app.mention))
        except RPCError as text_e:
            LOGGER(__name__).error(f"Failed to send initial text response after photo FloodWait: {text_e}")
            return # Exit if initial response cannot be sent
    except RPCError as e:
        LOGGER(__name__).error(f"Failed to send initial ping photo: {e}")
        return # Exit if initial response cannot be sent
    except Exception as e:
        LOGGER(__name__).error(f"An unexpected error occurred while sending initial ping photo: {e}")
        return

    # Ensure we have an initial_response object before proceeding
    if not initial_response:
        LOGGER(__name__).error("No initial response object available for ping command.")
        return

    # Concurrently gather system stats and Pyrogram ping
    # This slightly improves performance by running these tasks in parallel
    try:
        # Using asyncio.gather to run these potentially I/O bound tasks concurrently
        pytgping_task = Anony.ping()
        sys_stats_task = bot_sys_stats()

        pytgping, (UP, CPU, RAM, DISK) = await asyncio.gather(
            pytgping_task,
            sys_stats_task
        )
    except Exception as e:
        LOGGER(__name__).error(f"Error gathering system stats or Pyrogram ping: {e}")
        # Attempt to inform the user about the error
        try:
            await initial_response.edit_text(
                _["general_2"].format(f"Failed to retrieve bot stats: {e}"),
                reply_markup=supp_markup(_)
            )
        except RPCError as edit_e:
            LOGGER(__name__).error(f"Failed to edit message with error details: {edit_e}")
        return

    # Calculate response time
    response_time_ms = (datetime.now() - start_time).microseconds / 1000

    try:
        # Edit the message with the final ping results
        await initial_response.edit_text(
            _["ping_2"].format(response_time_ms, app.mention, UP, RAM, CPU, DISK, pytgping),
            reply_markup=supp_markup(_),
        )
    except FloodWait as e:
        LOGGER(__name__).warning(f"FloodWait encountered when editing ping message: {e.value} seconds.")
        # If edit fails due to flood, try replying with a new message
        try:
            await message.reply_text(
                _["ping_2"].format(response_time_ms, app.mention, UP, RAM, CPU, DISK, pytgping),
                reply_markup=supp_markup(_)
            )
        except RPCError as reply_e:
            LOGGER(__name__).error(f"Failed to send new reply after edit FloodWait: {reply_e}")
    except RPCError as e:
        LOGGER(__name__).error(f"Failed to edit ping message: {e}")
    except Exception as e:
        LOGGER(__name__).error(f"An unexpected error occurred while editing ping message: {e}")

