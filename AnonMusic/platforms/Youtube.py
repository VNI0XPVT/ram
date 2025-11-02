import asyncio, httpx, yt_dlp, os
import glob, re, random, json, requests

from typing import Union
from pyrogram.types import Message
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from pyrogram.enums import MessageEntityType
from concurrent.futures import ThreadPoolExecutor
from youtubesearchpython.__future__ import VideosSearch, CustomSearch

# Import config values
try:
    from config import BASE_API_URL, BASE_API_KEY
except ImportError:
    # Default values if config import fails
    BASE_API_URL = "http://194.182.64.17:1470"
    BASE_API_KEY = "sk_cQ2oq8b87we6IxOnJwjEUKbexHGh"

# Import fix for missing modules
try:
    from AnonMusic.utils.database import is_on_off
    from AnonMusic.utils.formatters import time_to_seconds
except ImportError:
    # Fallback functions if imports fail
    def is_on_off(*args):
        return True
    
    def time_to_seconds(time_str):
        """Convert time string (HH:MM:SS or MM:SS) to seconds"""
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
        return None
      
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


async def get_stream_url(query, video=False):
    """Get stream URL from API without downloading"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            params = {
                "query": query, 
                "video": str(video).lower(),
                "api_key": BASE_API_KEY
            }
            response = await client.get(f"{BASE_API_URL}/youtube", params=params)

            if response.status_code == 200:
                info = response.json()
                stream_url = info.get("stream_url")
                if stream_url:
                    return stream_url
                else:
                    print(f"❌ No stream_url in response: {info}")
                    return None
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Stream URL Error: {e}")
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

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
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                vidid = result["id"]
                if str(duration_min) == "None":
                    duration_sec = 0
                else:
                    duration_sec = int(time_to_seconds(duration_min))
                return title, duration_min, duration_sec, thumbnail, vidid
        except Exception as e:
            print(f"❌ Details Error: {e}")
            return "Unknown", "0:00", 0, "", ""

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["title"]
        except Exception as e:
            print(f"❌ Title Error: {e}")
            return "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["duration"]
        except Exception as e:
            print(f"❌ Duration Error: {e}")
            return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["thumbnails"][0]["url"].split("?")[0]
        except Exception as e:
            print(f"❌ Thumbnail Error: {e}")
            return ""

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """Get video stream URL without downloading"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        stream_url = await get_stream_url(link, True)
        if stream_url:
            return stream_url
        else:
            # Fallback to direct URL extraction if API fails
            try:
                ydl_opts = {
                    'format': 'best[height<=720]',
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    return info['url']
            except Exception as e:
                print(f"❌ Video URL Error: {e}")
                return None

    async def music(self, link: str, videoid: Union[bool, str] = None):
        """Get audio stream URL without downloading"""
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        stream_url = await get_stream_url(link, False)
        if stream_url:
            return stream_url
        else:
            # Fallback to direct URL extraction if API fails
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    return info['url']
            except Exception as e:
                print(f"❌ Music URL Error: {e}")
                return None

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
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
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                vidid = result["id"]
                yturl = result["link"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                
                track_details = {
                    "title": title,
                    "link": yturl,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }
                return track_details, vidid
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
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            ytdl_opts = {"quiet": True}
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                formats_available = []
                r = ydl.extract_info(link, download=False)
                for format in r["formats"]:
                    try:
                        if not "dash" in str(format["format"]).lower():
                            formats_available.append(
                                {
                                    "format": format.get("format", ""),
                                    "filesize": format.get("filesize", 0),
                                    "format_id": format.get("format_id", ""),
                                    "ext": format.get("ext", ""),
                                    "format_note": format.get("format_note", ""),
                                    "yturl": link,
                                }
                            )
                    except Exception:
                        continue
            return formats_available, link
        except Exception as e:
            print(f"❌ Formats Error: {e}")
            return [], link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        try:
            a = VideosSearch(link, limit=10)
            result = (await a.next()).get("result")
            if result and len(result) > query_type:
                title = result[query_type]["title"]
                duration_min = result[query_type]["duration"]
                vidid = result[query_type]["id"]
                thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
                return title, duration_min, thumbnail, vidid
            else:
                return "Unknown", "0:00", "", ""
        except Exception as e:
            print(f"❌ Slider Error: {e}")
            return "Unknown", "0:00", "", ""

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        """Download file or return stream URL"""
        if videoid:
            link = self.base + link
        
        # Use API for streaming without download
        if video:
            # Video stream
            stream_url = await get_stream_url(link, True)
            return stream_url, None
        else:
            # Audio stream  
            stream_url = await get_stream_url(link, False)
            return stream_url, None

        # Fallback to download if streaming fails
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

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            downloaded_file = await loop.run_in_executor(None, video_dl)
            return downloaded_file, None
        else:
            downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file, None
