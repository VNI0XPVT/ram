import asyncio, httpx, yt_dlp, os
import glob, re, random, json, requests
import aiofiles
from pathlib import Path
import time
import mimetypes

from typing import Union
from pyrogram.types import Message
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pyrogram.enums import MessageEntityType
from concurrent.futures import ThreadPoolExecutor
from youtubesearchpython.__future__ import VideosSearch, CustomSearch

from AnonMusic.utils.database import is_on_off
from AnonMusic.utils.formatters import time_to_seconds

# Create downloads directory if not exists
def ensure_downloads_dir():
    """Ensure downloads directory exists"""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    return downloads_dir

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    if not url:
        return url
    
    # If it's already a video ID (11 characters)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return url

def clean_filename(filename):
    """Clean filename by removing special characters"""
    # Remove special characters but keep spaces, hyphens, underscores
    cleaned = re.sub(r'[^\w\s-]', '', filename)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Trim and limit length
    return cleaned.strip()[:50]  # Limit to 50 characters

def cookie_txt_file():
    try:
        folder_path = f"{os.getcwd()}/cookies"
        filename = f"{os.getcwd()}/cookies/logs.csv"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in the specified folder.")
        cookie_txt_file = random.choice(txt_files)
        with open(filename, 'a') as file:
            file.write(f'Choosen File : {cookie_txt_file}\n')
        return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""
    except:
        pass
      
async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

async def download_from_stream_url(stream_url, filename, is_video=False):
    """Download media from stream URL to downloads folder"""
    try:
        ensure_downloads_dir()
        
        print(f"📥 Downloading from stream URL: {stream_url}")
        print(f"📝 Filename: {filename}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            # Don't use HEAD request (causes 405 error)
            # Directly try to download and check content type from response
            
            print("🎬 Starting direct download...")
            
            async with client.stream('GET', stream_url) as response:
                # Check content type from response
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                print(f"📦 Content-Type: {content_type}")
                print(f"📎 Content-Disposition: {content_disposition}")
                
                # Check if it's JSON (API error)
                if 'application/json' in content_type:
                    print("❌ Stream URL returns JSON, not media")
                    # Read the JSON error
                    try:
                        error_content = await response.aread()
                        error_info = json.loads(error_content)
                        print(f"❌ API Error: {error_info}")
                    except:
                        print("❌ Could not read error details")
                    return None
                
                # Determine file extension
                extension = ".mp4" if is_video else ".mp3"
                
                # Clean filename and add extension
                clean_name = clean_filename(filename)
                filepath = Path("downloads") / f"{clean_name}{extension}"
                
                print(f"💾 Saving to: {filepath}")
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                print(f"📏 Total size: {total_size} bytes")
                
                async with aiofiles.open(filepath, 'wb') as file:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Progress logging
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            if int(percent) % 25 == 0:  # Log every 25%
                                print(f"📊 Download progress: {percent:.1f}% ({downloaded_size}/{total_size} bytes)")
                
                # Verify file was downloaded
                if filepath.exists() and filepath.stat().st_size > 0:
                    file_size = filepath.stat().st_size
                    print(f"✅ Download completed: {filepath} ({file_size} bytes)")
                    return str(filepath)
                else:
                    print("❌ Downloaded file is empty or doesn't exist")
                    return None
                
    except httpx.TimeoutException:
        print("❌ Download timeout")
        return None
    except httpx.RequestError as e:
        print(f"❌ Download request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None

async def get_stream_url(query, video=False):
    """Get stream URL from API using video ID only"""
    apis = [
        {
            "url": "http://194.182.64.17:1470/youtube",
            "key": "sk_yvf4HYJxgQmzQDvf3MT4OOYbjSH6"
        }
    ]

    # Extract video ID from query
    video_id = extract_video_id(query)
    print(f"🎬 Using video ID: {video_id}")

    async with httpx.AsyncClient(timeout=60) as client:
        for api in apis:
            try:
                # Use proper boolean values for video parameter
                params = {
                    "query": video_id,  # Use only video ID, not full URL
                    "video": "true" if video else "false",  # Proper boolean string
                    "api_key": api["key"]
                }
                
                print(f"🔗 API Request: {api['url']}")
                print(f"📋 Params: {params}")
                
                response = await client.get(api["url"], params=params)
                print(f"📡 API Response Status: {response.status_code}")

                if response.status_code == 200:
                    info = response.json()
                    stream_url = info.get("stream_url")
                    if stream_url:
                        print(f"✅ Stream URL found: {stream_url}")
                        return stream_url
                    else:
                        print(f"❌ No stream_url in response: {info}")
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"❌ API Exception: {e}")
                continue

    return None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        ensure_downloads_dir()

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        # Extract video ID for search
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        try:
            results = VideosSearch(search_query, limit=1)
            search_results = await results.next()
            
            if not search_results["result"]:
                return "Unknown", "0:00", 0, "", ""
                
            result = search_results["result"][0]
            title = result.get("title", "Unknown")
            duration_min = result.get("duration", "0:00")
            thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
            vidid = result.get("id", "")
            
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
                
            return title, duration_min, duration_sec, thumbnail, vidid
            
        except Exception as e:
            print(f"❌ Details Error: {e}")
            return "Unknown", "0:00", 0, "", ""

    async def title(self, link: str, videoid: Union[bool, str] = None):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        try:
            results = VideosSearch(search_query, limit=1)
            search_results = await results.next()
            
            if search_results["result"]:
                return search_results["result"][0].get("title", "Unknown Title")
            return "Unknown Title"
            
        except Exception as e:
            print(f"❌ Title Error: {e}")
            return "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        try:
            results = VideosSearch(search_query, limit=1)
            search_results = await results.next()
            
            if search_results["result"]:
                return search_results["result"][0].get("duration", "0:00")
            return "0:00"
            
        except Exception as e:
            print(f"❌ Duration Error: {e}")
            return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        try:
            results = VideosSearch(search_query, limit=1)
            search_results = await results.next()
            
            if search_results["result"]:
                thumbnails = search_results["result"][0].get("thumbnails", [{}])
                if thumbnails:
                    return thumbnails[0].get("url", "").split("?")[0]
            return ""
            
        except Exception as e:
            print(f"❌ Thumbnail Error: {e}")
            return ""

    async def video(self, link: str, videoid: Union[bool, str] = None):
        # Extract video ID
        video_id = extract_video_id(link)
        return await get_stream_url(video_id, True)

    async def music(self, link: str, videoid: Union[bool, str] = None):
        # Extract video ID
        video_id = extract_video_id(link)
        return await get_stream_url(video_id, False)

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        try:
            results = VideosSearch(search_query, limit=1)
            search_results = await results.next()
            
            if not search_results["result"]:
                return {
                    "title": "Unknown",
                    "link": link,
                    "vidid": "",
                    "duration_min": "0:00",
                    "thumb": ""
                }, ""
                
            result = search_results["result"][0]
            track_details = {
                "title": result.get("title", "Unknown"),
                "link": result.get("link", link),
                "vidid": result.get("id", ""),
                "duration_min": result.get("duration", "0:00"),
                "thumb": result.get("thumbnails", [{}])[0].get("url", "").split("?")[0],
            }
            return track_details, result.get("id", "")
            
        except Exception as e:
            print(f"❌ Track Error: {e}")
            return {
                "title": "Unknown",
                "link": link,
                "vidid": "",
                "duration_min": "0:00",
                "thumb": ""
            }, ""

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(search_query, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": search_query,
                        }
                    )
        return formats_available, search_query

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        video_id = extract_video_id(link)
        search_query = video_id
        
        if videoid and not link.startswith("http"):
            search_query = self.base + search_query
            
        a = VideosSearch(search_query, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: bool = False,
        videoid: Union[bool, str] = None,
        songaudio: bool = False,
        songvideo: bool = False,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        # Extract video ID
        video_id = extract_video_id(link)
        print(f"🎬 Processing video ID: {video_id}")
        
        # Get video details for filename
        try:
            video_title, _, _, _, vidid = await self.details(link)
            # Clean filename properly
            clean_title = clean_filename(video_title)
            filename = f"{vidid}_{clean_title}" if clean_title else vidid
            print(f"📝 Generated filename: {filename}")
        except Exception as e:
            print(f"❌ Error getting video details: {e}")
            # Fallback filename
            filename = f"download_{int(time.time())}"
        
        # First try stream URL download
        stream_url = await get_stream_url(video_id, video)
        if stream_url:
            print(f"🎯 Using stream URL: {stream_url}")
            downloaded_file = await download_from_stream_url(stream_url, filename, video)
            if downloaded_file:
                return downloaded_file, None
            else:
                print("❌ Stream download failed")
        else:
            print("❌ No stream URL found")
        
        # Fallback to traditional download if stream fails
        print("🔄 Using traditional download...")
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        if songvideo:
            downloaded_file = await loop.run_in_executor(None, video_dl)
            return downloaded_file, None
        elif songaudio:
            downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file, None
        elif video:
            downloaded_file = await loop.run_in_executor(None, video_dl)
            return downloaded_file, None
        else:
            downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file, None

# Create global instance
youtube = YouTubeAPI()
