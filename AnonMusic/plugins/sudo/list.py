import io
import os
import time
import shutil
import mimetypes
from inspect import signature
from os.path import exists, isdir, join, getsize, getmtime, getatime

from pyrogram import filters
from pyrogram.types import Message, InputMediaDocument

from AnonMusic import app
from AnonMusic.misc import SUDOERS

# Constants
MAX_MESSAGE_SIZE_LIMIT = 4095
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_PREVIEW_SIZE = 2 * 1024 * 1024  # 2 MB for text file previews

# File type icons mapping
FILE_ICONS = {
    'audio': '🎵',
    'video': '🎞',
    'image': '🖼',
    'archive': '🗜',
    'executable': '⚙️',
    'disk': '💿',
    'android': '📱',
    'python': '🐍',
    'document': '📄',
    'text': '📝',
    'code': '💻',
    'config': '⚙️',
    'font': '🔤',
    'database': '🗄'
}

# File extensions mapping
EXTENSION_MAP = {
    # Audio
    '.mp3': 'audio', '.flac': 'audio', '.wav': 'audio', '.m4a': 'audio',
    '.opus': 'audio', '.ogg': 'audio', '.aac': 'audio',
    
    # Video
    '.mkv': 'video', '.mp4': 'video', '.webm': 'video', '.avi': 'video',
    '.mov': 'video', '.flv': 'video', '.wmv': 'video',
    
    # Images
    '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
    '.bmp': 'image', '.ico': 'image', '.webp': 'image', '.svg': 'image',
    '.tiff': 'image',
    
    # Archives
    '.zip': 'archive', '.tar': 'archive', '.tar.gz': 'archive', '.rar': 'archive',
    '.7z': 'archive', '.xz': 'archive', '.bz2': 'archive', '.gz': 'archive',
    
    # Executables
    '.exe': 'executable', '.deb': 'executable', '.rpm': 'executable',
    '.msi': 'executable', '.appimage': 'executable', '.dmg': 'executable',
    
    # Disk images
    '.iso': 'disk', '.img': 'disk', '.vmdk': 'disk',
    
    # Android
    '.apk': 'android', '.xapk': 'android', '.aab': 'android',
    
    # Python
    '.py': 'python', '.pyc': 'python', '.pyo': 'python', '.pyd': 'python',
    
    # Documents
    '.pdf': 'document', '.doc': 'document', '.docx': 'document',
    '.xls': 'document', '.xlsx': 'document', '.ppt': 'document',
    '.pptx': 'document', '.odt': 'document', '.ods': 'document',
    
    # Text/code files
    '.txt': 'text', '.log': 'text', '.csv': 'text',
    '.json': 'code', '.xml': 'code', '.html': 'code', '.css': 'code',
    '.js': 'code', '.ts': 'code', '.php': 'code', '.sh': 'code',
    '.bat': 'code', '.cmd': 'code', '.c': 'code', '.cpp': 'code',
    '.h': 'code', '.java': 'code', '.kt': 'code', '.go': 'code',
    '.rs': 'code', '.rb': 'code', '.pl': 'code', '.lua': 'code',
    
    # Config files
    '.ini': 'config', '.cfg': 'config', '.conf': 'config', '.yml': 'config',
    '.yaml': 'config', '.toml': 'config', '.env': 'config',
    
    # Fonts
    '.ttf': 'font', '.otf': 'font', '.woff': 'font', '.woff2': 'font',
    
    # Databases
    '.db': 'database', '.sqlite': 'database', '.sql': 'database',
    '.dump': 'database', '.mdb': 'database'
}

def humanbytes(size: int) -> str:
    """Convert bytes into a human-readable format."""
    if not size:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} {units[-1]}"

def humantime(seconds: float) -> str:
    """Convert seconds into a human-readable time format."""
    intervals = (
        ('weeks', 604800),
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1)
    )
    
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append(f"{int(value)} {name}")
    return ', '.join(result[:3]) if result else "0 seconds"

def get_file_icon(filename: str) -> str:
    """Get appropriate icon for a file based on its extension."""
    _, ext = os.path.splitext(filename.lower())
    file_type = EXTENSION_MAP.get(ext, None)
    
    if not file_type:
        # Try to guess from mime type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            main_type = mime_type.split('/')[0]
            if main_type in ['audio', 'video', 'image']:
                file_type = main_type
            elif main_type == 'text':
                file_type = 'text' if ext in ['.txt', '.log'] else 'code'
    
    return FILE_ICONS.get(file_type or 'document', '📄')

def split_limits(text: str, limit: int = MAX_MESSAGE_SIZE_LIMIT) -> list:
    """Split text into chunks that do not exceed the given limit."""
    return [text[i:i + limit] for i in range(0, len(text), limit)]

async def eor(msg: Message, **kwargs) -> Message:
    """Edit or reply to a message."""
    func = msg.edit_text if msg.from_user and msg.from_user.is_self else msg.reply
    
    # Get valid arguments for the function
    valid_args = signature(func).parameters.keys()
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_args}
    
    return await func(**filtered_kwargs)

def capture_err(func):
    """Decorator to handle errors gracefully."""
    async def wrapper(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            error_msg = f"<b>⚠️ Error:</b> <code>{str(e)}</code>"
            if len(error_msg) > MAX_MESSAGE_SIZE_LIMIT:
                with io.BytesIO(str.encode(error_msg)) as error_file:
                    error_file.name = "error_log.txt"
                    await message.reply_document(
                        error_file,
                        caption="Error log is too large to display"
                    )
            else:
                await eor(message, text=error_msg)
            raise e
    return wrapper

@app.on_message(filters.command(["ls", "list"]) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@capture_err
async def list_files(_, message: Message):
    """List files and directories with detailed information."""
    path = os.getcwd()
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        path = args[1].strip()
        # Expand ~ to home directory
        path = os.path.expanduser(path)
    
    if not exists(path):
        await eor(
            message,
            text=f"<b>❌ No such path :</b> <code>{path}</code>"
        )
        return
    
    if isdir(path):
        # List directory contents
        msg = f"<b>📂 Directory Listing :</b> <code>{path}</code>\n\n"
        files = []
        folders = []
        
        try:
            for item in sorted(os.listdir(path)):
                item_path = join(path, item)
                if isdir(item_path):
                    folders.append(f"📁 <code>{item}/</code>")
                else:
                    icon = get_file_icon(item)
                    files.append(f"{icon} <code>{item}</code>")
            
            if folders or files:
                if folders:
                    msg += "<b>📁 Folders:</b>\n" + '\n'.join(folders) + '\n\n'
                if files:
                    msg += "<b>📄 Files:</b>\n" + '\n'.join(files)
            else:
                msg += "<code>Empty directory</code>"
            
            # Add summary
            total_items = len(folders) + len(files)
            msg += f"\n\n<b>Total items:</b> {total_items}"
            
        except PermissionError:
            msg += "<code>Permission denied</code>"
    else:
        # Show file details
        size = getsize(path)
        mtime = getmtime(path)
        atime = getatime(path)
        icon = get_file_icon(path)
        
        msg = (
            f"{icon} <b>File Details:</b> <code>{path}</code>\n\n"
            f"• <b>Size:</b> <code>{humanbytes(size)}</code>\n"
            f"• <b>Modified:</b> <code>{time.ctime(mtime)}</code>\n"
            f"• <b>Accessed:</b> <code>{time.ctime(atime)}</code>\n"
        )
        
        # Add preview for text files under 2MB
        if size < MAX_PREVIEW_SIZE:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1000 chars
                    if content.strip():
                        msg += f"\n<b>Preview:</b>\n<code>\n{content}\n</code>"
            except:
                pass
    
    if len(msg) > MAX_MESSAGE_SIZE_LIMIT:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = f"ls_{os.path.basename(path)}.txt"
            await message.reply_document(
                out_file,
                caption=f"<b>📂 Contents of</b> <code>{path}</code>"
            )
            await message.delete()
    else:
        await eor(message, text=msg)

@app.on_message(filters.command(["rm", "del", "delete"]) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@capture_err
async def delete_file(_, message: Message):
    """Delete files or directories."""
    if len(message.command) < 2:
        return await eor(message, text="<b>❌ Usage:</b> <code>/rm &lt;path&gt;</code>")
    
    path = message.text.split(maxsplit=1)[1].strip()
    path = os.path.expanduser(path)
    
    if not exists(path):
        return await eor(message, text=f"<b>❌ Path not found:</b> <code>{path}</code>")
    
    try:
        if isdir(path):
            shutil.rmtree(path)
            await eor(message, text=f"<b>✅ Deleted directory:</b> <code>{path}</code>")
        else:
            os.remove(path)
            await eor(message, text=f"<b>✅ Deleted file:</b> <code>{path}</code>")
    except Exception as e:
        await eor(message, text=f"<b>❌ Error deleting</b> <code>{path}</code>: <code>{str(e)}</code>")

@app.on_message(filters.command(["upload", "up"]) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@capture_err
async def upload_file(_, message: Message):
    """Upload a file to the server."""
    if not message.reply_to_message or not message.reply_to_message.document:
        return await eor(message, text="<b>❌ Please reply to a file with this command.</b>")
    
    if len(message.command) < 2:
        return await eor(message, text="<b>❌ Usage:</b> <code>/upload &lt;destination_path&gt;</code>")
    
    dest_path = message.command[1].strip()
    dest_path = os.path.expanduser(dest_path)
    
    if os.path.isdir(dest_path):
        return await eor(message, text="<b>❌ Destination path must include a filename.</b>")
    
    doc = message.reply_to_message.document
    
    if doc.file_size > MAX_FILE_SIZE:
        return await eor(
            message,
            text=f"<b>❌ File too large.</b> Max size: <code>{humanbytes(MAX_FILE_SIZE)}</code>"
        )
    
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Download and save the file
        download_msg = await eor(message, text="<b>⬇️ Downloading file...</b>")
        downloaded_path = await message.reply_to_message.download()
        
        await download_msg.edit_text("<b>💾 Saving file...</b>")
        shutil.move(downloaded_path, dest_path)
        
        size = getsize(dest_path)
        await download_msg.edit_text(
            f"<b>✅ File saved successfully!</b>\n\n"
            f"• <b>Path:</b> <code>{dest_path}</code>\n"
            f"• <b>Size:</b> <code>{humanbytes(size)}</code>"
        )
    except Exception as e:
        await eor(message, text=f"<b>❌ Error uploading file:</b> <code>{str(e)}</code>")
        # Clean up if something went wrong
        if 'downloaded_path' in locals() and exists(downloaded_path):
            os.remove(downloaded_path)

@app.on_message(filters.command(["mkdir", "md"]) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@capture_err
async def make_directory(_, message: Message):
    """Create a new directory."""
    if len(message.command) < 2:
        return await eor(message, text="<b>❌ Usage:</b> <code>/mkdir &lt;directory_path&gt;</code>")
    
    path = message.command[1].strip()
    path = os.path.expanduser(path)
    
    if exists(path):
        return await eor(message, text=f"<b>❌ Path already exists:</b> <code>{path}</code>")
    
    try:
        os.makedirs(path)
        await eor(message, text=f"<b>✅ Created directory:</b> <code>{path}</code>")
    except Exception as e:
        await eor(message, text=f"<b>❌ Error creating directory:</b> <code>{str(e)}</code>")

@app.on_message(filters.command(["stat", "lsinfo"]) & ~filters.forwarded & ~filters.via_bot & SUDOERS)
@capture_err
async def file_stats(_, message: Message):
    """Show detailed statistics about a file or directory."""
    if len(message.command) < 2:
        return await eor(message, text="<b>❌ Usage:</b> <code>/stat &lt;path&gt;</code>")
    
    path = message.command[1].strip()
    path = os.path.expanduser(path)
    
    if not exists(path):
        return await eor(message, text=f"<b>❌ Path not found:</b> <code>{path}</code>")
    
    try:
        if isdir(path):
            # Directory statistics
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(path):
                dir_count += len(dirs)
                file_count += len(files)
                for f in files:
                    fp = join(root, f)
                    total_size += getsize(fp) if exists(fp) else 0
            
            stat_msg = (
                f"<b>📂 Directory Stats:</b> <code>{path}</code>\n\n"
                f"• <b>Total size:</b> <code>{humanbytes(total_size)}</code>\n"
                f"• <b>Files:</b> <code>{file_count}</code>\n"
                f"• <b>Subdirectories:</b> <code>{dir_count}</code>\n"
                f"• <b>Last modified:</b> <code>{time.ctime(getmtime(path))}</code>\n"
                f"• <b>Permissions:</b> <code>{oct(os.stat(path).st_mode)[-3:]}</code>"
            )
        else:
            # File statistics
            stat = os.stat(path)
            size = getsize(path)
            mtime = getmtime(path)
            atime = getatime(path)
            icon = get_file_icon(path)
            
            stat_msg = (
                f"{icon} <b>File Stats:</b> <code>{path}</code>\n\n"
                f"• <b>Size:</b> <code>{humanbytes(size)}</code>\n"
                f"• <b>Type:</b> <code>{mimetypes.guess_type(path)[0] or 'Unknown'}</code>\n"
                f"• <b>Modified:</b> <code>{time.ctime(mtime)}</code>\n"
                f"• <b>Accessed:</b> <code>{time.ctime(atime)}</code>\n"
                f"• <b>Permissions:</b> <code>{oct(stat.st_mode)[-3:]}</code>\n"
                f"• <b>Owner UID:</b> <code>{stat.st_uid}</code>\n"
                f"• <b>Group GID:</b> <code>{stat.st_gid}</code>"
            )
        
        await eor(message, text=stat_msg)
    except Exception as e:
        await eor(message, text=f"<b>❌ Error getting stats:</b> <code>{str(e)}</code>")
