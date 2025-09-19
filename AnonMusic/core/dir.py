import os
import traceback

from ..logging import LOGGER

def dirr():
    try:
        deleted_files = 0
        for file in os.listdir():
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    os.remove(file)
                    deleted_files += 1
                except Exception as e:
                    LOGGER(__name__).warning(f"⚠️ Failed to delete {file}: {e}")

        for folder in ["downloads", "cache"]:
            if not os.path.exists(folder):
                try:
                    os.mkdir(folder)
                    LOGGER(__name__).info(f"📁 Created missing directory: {folder}")
                except Exception as e:
                    LOGGER(__name__).error(f"❌ Failed to create {folder}: {e}")

        LOGGER(__name__).info(f"🧹 Cleaned {deleted_files} image file(s).")
        LOGGER(__name__).info("✅ Directory check/update complete.")

    except Exception as e:
        LOGGER(__name__).error("❌ An unexpected error occurred in dirr()")
        LOGGER(__name__).error(traceback.format_exc())
