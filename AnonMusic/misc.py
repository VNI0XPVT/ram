import socket
import time
import heroku3
from pyrogram import filters

import config
from AnonMusic.core.mongo import mongodb
from .logging import LOGGER

# Globals
SUDOERS = filters.user()
HAPP = None
_boot_ = time.time()


def is_heroku():
    """Check if environment is Heroku."""
    try:
        return "heroku" in socket.getfqdn()
    except Exception as e:
        LOGGER(__name__).warning(f"Failed to determine host environment: {e}")
        return False


XCB = [
    "/", "@", ".", "com", ":", "git", "heroku", "push",
    str(config.HEROKU_API_KEY), "https", str(config.HEROKU_APP_NAME),
    "HEAD", "Master",
]


def dbb():
    """Initialize local DB fallback."""
    global db
    db = {}
    LOGGER(__name__).info("✅ Local in-memory database initialized.")


async def sudo():
    """Load or initialize sudoers list from MongoDB."""
    global SUDOERS
    try:
        SUDOERS.add(config.OWNER_ID)
        sudoersdb = mongodb.sudoers

        sudo_data = await sudoersdb.find_one({"sudo": "sudo"}) or {}
        sudoers = sudo_data.get("sudoers", [])

        if config.OWNER_ID not in sudoers:
            sudoers.append(config.OWNER_ID)
            await sudoersdb.update_one(
                {"sudo": "sudo"},
                {"$set": {"sudoers": sudoers}},
                upsert=True,
            )

        for user_id in sudoers:
            SUDOERS.add(user_id)

        LOGGER(__name__).info(f"✅ Loaded {len(sudoers)} sudo users.")
    except Exception as e:
        LOGGER(__name__).error(f"⚠️ Failed to load sudoers: {e}")


def heroku():
    """Configure Heroku app instance if on Heroku."""
    global HAPP
    if not is_heroku():
        LOGGER(__name__).info("💻 Not running on Heroku.")
        return

    if not config.HEROKU_API_KEY or not config.HEROKU_APP_NAME:
        LOGGER(__name__).warning("⚠️ Heroku credentials are missing in config.")
        return

    try:
        heroku_conn = heroku3.from_key(config.HEROKU_API_KEY)
        HAPP = heroku_conn.app(config.HEROKU_APP_NAME)
        LOGGER(__name__).info("✅ Heroku app configured successfully.")
    except Exception as e:
        LOGGER(__name__).error(f"⚠️ Failed to configure Heroku app: {e}")
