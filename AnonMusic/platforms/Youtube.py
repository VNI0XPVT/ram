import asyncio, httpx, yt_dlp, os
import glob, re, random, json, requests

from typing import Union
from pyrogram.types import Message
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pyrogram.enums import MessageEntityType
from concurrent.futures import ThreadPoolExecutor
from youtubesearchpython.__future__ import VideosSearch, CustomSearch

from AnonMusic.utils.database import is_on_off
from AnonMusic.utils.formatters import time_to_seconds

# ===== CONFIGURATION =====
BASE_API_URL = "http://194.182.64.17:1470"
BASE_API_KEY = "sk_yvf4HYJxgQmzQDvf3MT4OOYbjSH6"

# ===== FALLBACK FUNCTIONS =====
def is_on_off(*args):
    """Fallback function if import fails"""
    return True

def time_to_seconds(time_str):
    """Convert time string to seconds"""
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        else:  # SS
            return parts[0]
    except:
        return 0

def cookie_txt_file():
    """Get random cookie file"""
    try:
        folder_path = f"{os.getcwd()}/cookies"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            return None
        cookie_txt_file = random.choice(txt_files)
        return f"cookies/{str(cookie_txt_file).split('/')[-1]}"
    except:
        return None

async def shell_cmd(cmd):
    """Execute shell command"""
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

async def get_stream_url(query, video=False):
    """Get stream URL from API with fallback to direct extraction"""
    print(f"🎵 Fetching stream URL for: {query} (video: {video})")
    
    # Clean the URL first
    clean_query = clean_youtube_url(query)
    print(f"🔧 Cleaned URL: {clean_query}")
    
    # Try API first
    api_url = await get_stream_url_from_api(clean_query, video)
    if api_url:
        return api_url
    
    # Fallback to direct yt-dlp extraction
    print("🔄 API failed, using direct yt-dlp extraction...")
    return await get_stream_url_direct(clean_query, video)

def clean_youtube_url(url):
    """Clean and normalize YouTube URL"""
    if not url:
        return url
    
    # Remove double encoding
    if "watch?v=https://" in url:
        # Extract the actual video ID
        match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    # If it's already a proper YouTube URL, return as is
    if "youtube.com/watch?v=" in url or "youtu.be/" in url:
        return url
    
    # If it's just a video ID, make it a full URL
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return f"https://www.youtube.com/watch?v={url}"
    
    return url

async def get_stream_url_from_api(query, video=False):
    """Get stream URL from your API"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            params = {
                "query": query, 
                "video": str(video).lower(),
                "api_key": BASE_API_KEY
            }
            
            print(f"🔗 API Request: {BASE_API_URL}/youtube")
            print(f"📋 Params: query={params['query'][:50]}..., video={params['video']}")
            
            response = await client.get(f"{BASE_API_URL}/youtube", params=params)
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                info = response.json()
                stream_url = info.get("stream_url")
                if stream_url:
                    print(f"✅ Stream URL found: {stream_url[:100]}...")
                    return stream_url
                else:
                    print(f"❌ No stream_url in API response")
                    return None
            elif response.status_code == 403:
                print("❌ API Error 403: Access Forbidden - Invalid API Key or IP blocked")
                return None
            elif response.status_code == 429:
                print("❌ API Error 429: Rate Limit Exceeded")
                return None
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
    except httpx.ConnectError:
        print("❌ API Connection Error: Cannot connect to API server")
        return None
    except httpx.TimeoutException:
        print("❌ API Timeout: Request took too long")
        return None
    except Exception as e:
        print(f"❌ API Unknown Error: {e}")
        return None

async def get_stream_url_direct(query, video=False):
    """Fallback: Get stream URL directly using yt-dlp"""
    try:
        if video:
            ydl_opts = {
                'format': 'best[height<=720]',
                'quiet': True,
                'no_warnings': True,
            }
        else:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🎬 Extracting direct URL with yt-dlp: {query}")
            info = ydl.extract_info(query, download=False)
            direct_url = info.get('url')
            
            if direct_url:
                print(f"✅ Direct URL extracted: {direct_url[:100]}...")
                return direct_url
            else:
                print("❌ No URL found in yt-dlp extraction")
                return None
                
    except yt_dlp.DownloadError as e:
        print(f"❌ yt-dlp Download Error: {e}")
        return None
    except Exception as e:
        print(f"❌ yt-dlp Unknown Error: {e}")
        return None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        """Check if YouTube link exists"""
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        """Extract URL from message"""
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        
        text = ""
        offset = None
        length = None
        
        for message in messages:
            if offset:
                break
                
            # Check message entities
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            
            # Check caption entities  
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        
        if offset is None:
            return None
            
        return text[offset:offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        """Get video details"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            results = VideosSearch(link, limit=1)
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
                duration_sec = time_to_seconds(duration_min)
                
            return title, duration_min, duration_sec, thumbnail, vidid
            
        except Exception as e:
            print(f"❌ Details Error: {e}")
            return "Unknown", "0:00", 0, "", ""

    async def title(self, link: str, videoid: Union[bool, str] = None):
        """Get video title"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        try:
            results = VideosSearch(link, limit=1)
            search_results = await results.next()
            
            if search_results["result"]:
                return search_results["result"][0].get("title", "Unknown Title")
            return "Unknown Title"
            
        except Exception as e:
            print(f"❌ Title Error: {e}")
            return "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        """Get video duration"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        try:
            results = VideosSearch(link, limit=1)
            search_results = await results.next()
            
            if search_results["result"]:
                return search_results["result"][0].get("duration", "0:00")
            return "0:00"
            
        except Exception as e:
            print(f"❌ Duration Error: {e}")
            return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        """Get video thumbnail"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        try:
            results = VideosSearch(link, limit=1)
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
        """Get video stream URL"""
        # Fix: Don't double encode the URL
        if videoid and not link.startswith("http"):
            link = self.base + link
            
        print(f"🎥 Getting video stream for: {link}")
        stream_url = await get_stream_url(link, True)
        
        if not stream_url:
            print("❌ Failed to get video stream URL")
            return None
            
        return stream_url

    async def music(self, link: str, videoid: Union[bool, str] = None):
        """Get audio stream URL"""
        # Fix: Don't double encode the URL
        if videoid and not link.startswith("http"):
            link = self.base + link
            
        print(f"🎵 Getting audio stream for: {link}")
        stream_url = await get_stream_url(link, False)
        
        if not stream_url:
            print("❌ Failed to get audio stream URL")
            return None
            
        return stream_url

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        """Get playlist items"""
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            playlist = await shell_cmd(
                f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
            )
            result = playlist.split("\n")
            # Remove empty strings
            result = [item for item in result if item.strip()]
            return result
        except Exception as e:
            print(f"❌ Playlist Error: {e}")
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        """Get track details"""
        if videoid and not link.startswith("http"):
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            results = VideosSearch(link, limit=1)
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
        """Get available formats"""
        if videoid and not link.startswith("http"):
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            ytdl_opts = {"quiet": True}
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            with ydl:
                formats_available = []
                r = ydl.extract_info(link, download=False)
                
                for format_item in r.get("formats", []):
                    try:
                        if "dash" not in str(format_item.get("format", "")).lower():
                            formats_available.append({
                                "format": format_item.get("format", ""),
                                "filesize": format_item.get("filesize", 0),
                                "format_id": format_item.get("format_id", ""),
                                "ext": format_item.get("ext", ""),
                                "format_note": format_item.get("format_note", ""),
                                "yturl": link,
                            })
                    except Exception:
                        continue
                        
            return formats_available, link
            
        except Exception as e:
            print(f"❌ Formats Error: {e}")
            return [], link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        """Get slider data"""
        if videoid and not link.startswith("http"):
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            search = VideosSearch(link, limit=10)
            results = await search.next()
            result_list = results.get("result", [])
            
            if result_list and len(result_list) > query_type:
                item = result_list[query_type]
                return (
                    item.get("title", "Unknown"),
                    item.get("duration", "0:00"),
                    item.get("thumbnails", [{}])[0].get("url", "").split("?")[0],
                    item.get("id", "")
                )
            return "Unknown", "0:00", "", ""
            
        except Exception as e:
            print(f"❌ Slider Error: {e}")
            return "Unknown", "0:00", "", ""

    async def download(self, link: str, mystic, video: bool = False, videoid: Union[bool, str] = None,
                     songaudio: bool = False, songvideo: bool = False, 
                     format_id: str = None, title: str = None):
        """Download or stream media"""
        # Fix: Don't double encode the URL
        if videoid and not link.startswith("http"):
            link = self.base + link
        
        print(f"📥 Download request: {link} (video: {video})")
        
        # Use streaming (no download)
        if video:
            stream_url = await self.video(link, videoid)
        else:
            stream_url = await self.music(link, videoid)
            
        if stream_url:
            print(f"✅ Stream URL ready: {stream_url[:100]}...")
            return stream_url, None
        else:
            print("❌ Failed to get stream URL")
            return None, None

# Create global instance
youtube = YouTubeAPI()
