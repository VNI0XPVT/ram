import asyncio
import glob
import json
import os
import random
import re
import string
from typing import Optional, Tuple, Union, Dict, Any, List

import base64  # still imported for backward compat / future use
import requests
import yt_dlp

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch, CustomSearch

from AnonMusic import LOGGER
from AnonMusic.utils.database import is_on_off  # imported but not currently used
from AnonMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

# ---------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------

def cookie_txt_file() -> Optional[str]:
    """
    Pick a random cookie .txt file from ./cookies to help yt-dlp bypass rate limits.
    If none found, return None (yt-dlp will then run without --cookies).
    We also log which cookie file we picked for debugging.
    """
    try:
        folder_path = os.path.join(os.getcwd(), "cookies")
        log_file = os.path.join(folder_path, "logs.csv")
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            logger.warning("cookie_txt_file(): no cookie .txt found in ./cookies")
            return None
        choice = random.choice(txt_files)
        try:
            with open(log_file, "a") as f:
                f.write(f"Chosen File : {choice}\n")
        except Exception as log_err:
            logger.debug(f"cookie_txt_file(): failed to write log: {log_err}")
        return os.path.join("cookies", os.path.basename(choice))
    except Exception as e:
        logger.error(f"cookie_txt_file(): error while selecting cookie file: {e}")
        return None


def sanitize_link(raw: str) -> str:
    """
    Normalize YouTube URL / ID inputs:
    - strip playlist/time/query junk (&, ?si= etc.)
    - if the caller passed a bare video id, keep as-is (higher layers prepend base).
    """
    link = raw.strip()
    # remove extra params commonly appended by Telegram / share links
    for sep in ["&si=", "?si=", "&", "?"]:
        if sep in link:
            link = link.split(sep)[0]
    return link


def duration_to_secs_hard(duration_str: str) -> Optional[int]:
    """
    Convert duration like "HH:MM:SS" or "MM:SS" into seconds.
    Return None if it can't be parsed.
    """
    if not duration_str:
        return None
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
    except (ValueError, IndexError):
        return None
    return None


def create_session() -> requests.Session:
    """
    Session with basic retry logic. Reused in download() helpers.
    """
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


async def shell_cmd(cmd: str) -> str:
    """
    Run a shell command and return stdout/stderr in a controlled way.
    Special-case yt-dlp 'unavailable videos are hidden' noise.
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if err:
        stderr_txt = err.decode("utf-8", errors="ignore").lower()
        if "unavailable videos are hidden" in stderr_txt:
            return out.decode("utf-8", errors="ignore")
        return err.decode("utf-8", errors="ignore")
    return out.decode("utf-8", errors="ignore")


async def check_file_size(link: str) -> Optional[int]:
    """
    Ask yt-dlp (with cookies if available) for all formats and sum file sizes.
    Returns total size in bytes or None on failure.
    WARNING: This spawns yt-dlp, so it's not cheap.
    """

    async def get_format_info(l: str) -> Optional[Dict[str, Any]]:
        args = ["yt-dlp", "-J", l]
        ck = cookie_txt_file()
        if ck:
            args[1:1] = ["--cookies", ck]

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f"check_file_size(): yt-dlp -J failed: {stderr.decode(errors='ignore')}")
            return None
        try:
            return json.loads(stdout.decode())
        except Exception as e:
            logger.error(f"check_file_size(): invalid JSON from yt-dlp -J: {e}")
            return None

    def parse_size(formats: List[Dict[str, Any]]) -> int:
        total = 0
        for fmt in formats:
            size = fmt.get("filesize")
            if size:
                total += size
        return total

    info = await get_format_info(link)
    if not info:
        return None
    fmts = info.get("formats", [])
    if not fmts:
        logger.warning("check_file_size(): no formats in info")
        return None
    return parse_size(fmts)


# ---------------------------------------------------------------------------------
# YouTube API wrapper
# ---------------------------------------------------------------------------------

class YouTubeAPI:
    def __init__(self) -> None:
        self.base_watch = "https://www.youtube.com/watch?v="
        self.regex_host = r"(?:youtube\.com|youtu\.be)"
        self.list_base = "https://youtube.com/playlist?list="
        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,   # keeping names from old code for compatibility
            "cookie_downloads": 0,
            "existing_files": 0,
        }

    # ------------------------------
    # Internal search helper
    # ------------------------------
    async def _get_video_details(self, query: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Try to get a valid (<=1h) video result for "query" using youtubesearchpython.
        Falls back from VideosSearch to CustomSearch.
        Returns None if nothing valid.
        """
        try:
            # First pass: VideosSearch
            vs = VideosSearch(query, limit=limit)
            results = (await vs.next()).get("result", [])
            for item in results:
                dur_txt = item.get("duration", "0:00")
                dur_secs = duration_to_secs_hard(dur_txt) or 0
                if dur_secs <= 3600:
                    return item

            # Second pass: CustomSearch (slightly different algo)
            cs = CustomSearch(query=query, searchPreferences="EgIYAw==", limit=1)
            for item in (await cs.next()).get("result", []):
                return item

            return None
        except Exception as e:
            logger.error(f"_get_video_details(): {e}")
            return None

    # ------------------------------
    # Utilities for reading Telegram message
    # ------------------------------
    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        lnk = self.base_watch + link if videoid else link
        return bool(re.search(self.regex_host, lnk))

    async def url(self, message_1: Message) -> Optional[str]:
        """
        Try to pull a YouTube URL from a message or replied message.
        Returns first URL found or None.
        """
        msgs = [message_1]
        if message_1.reply_to_message:
            msgs.append(message_1.reply_to_message)

        for msg in msgs:
            # direct clickable URL entity
            if msg.entities:
                txt = msg.text or msg.caption or ""
                for ent in msg.entities:
                    if ent.type == MessageEntityType.URL:
                        return txt[ent.offset : ent.offset + ent.length]
            # telegram style text-link entity (caption)
            if msg.caption_entities:
                for ent in msg.caption_entities:
                    if ent.type == MessageEntityType.TEXT_LINK:
                        return ent.url
        return None

    # ------------------------------
    # Metadata helpers (title, duration, thumbnail, etc.)
    # ------------------------------
    async def _details_common(self, raw_link: str, videoid: Union[bool, str] = None) -> Dict[str, Any]:
        link = sanitize_link(self.base_watch + raw_link if videoid else raw_link)
        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")
        return result

    async def details(self, link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]:
        data = await self._details_common(link, videoid)
        title = data["title"]
        duration_min = data.get("duration")
        thumb = data["thumbnails"][0]["url"].split("?")[0]
        vidid = data["id"]
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumb, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        data = await self._details_common(link, videoid)
        return data["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        data = await self._details_common(link, videoid)
        return data["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        data = await self._details_common(link, videoid)
        return data["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None) -> Tuple[int, str]:
        """
        Return (ok_flag, direct_video_url) using yt-dlp -g best<=720p.
        ok_flag = 1 if success, 0 if fail.
        """
        link_norm = sanitize_link(self.base_watch + link if videoid else link)
        ck = cookie_txt_file()
        args = ["yt-dlp"]
        if ck:
            args += ["--cookies", ck]
        args += [
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            link_norm,
        ]
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            url_out = stdout.decode(errors="ignore").split("\n")[0]
            return 1, url_out
        return 0, stderr.decode(errors="ignore")

    async def playlist(self, link: str, limit: int, user_id: Union[str, int], videoid: Union[bool, str] = None) -> List[str]:
        """
        Return up to `limit` video IDs from a playlist using yt-dlp --flat-playlist.
        NOTE: user_id currently unused but kept for compatibility.
        """
        link_norm = sanitize_link(self.list_base + link if videoid else link)
        ck = cookie_txt_file()
        cookie_arg = f"--cookies {ck}" if ck else ""
        cmd = (
            f"yt-dlp -i --get-id --flat-playlist {cookie_arg} "
            f"--playlist-end {limit} --skip-download {link_norm}"
        ).strip()
        output = await shell_cmd(cmd)
        items = [x for x in output.split("\n") if x.strip()]
        return items

    async def track(self, link: str, videoid: Union[bool, str] = None) -> Tuple[Dict[str, Any], str]:
        data = await self._details_common(link, videoid)
        track_details = {
            "title": data["title"],
            "link": data["link"],
            "vidid": data["id"],
            "duration_min": data["duration"],
            "thumb": data["thumbnails"][0]["url"].split("?")[0],
        }
        return track_details, data["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Return a list of available formats (excluding dash-only), including filesize etc.
        Uses yt_dlp to fetch metadata without downloading.
        """
        link_norm = sanitize_link(self.base_watch + link if videoid else link)
        ytdl_opts = {
            "quiet": True,
            "cookiefile": cookie_txt_file(),
        }
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        formats_available: List[Dict[str, Any]] = []
        info = ydl.extract_info(link_norm, download=False)
        for fmt in info.get("formats", []):
            # skip DASH-only formats, keep muxed/progressive etc.
            if "dash" in str(fmt.get("format", "")).lower():
                continue
            needed = ("format", "filesize", "format_id", "ext", "format_note")
            if not all(k in fmt for k in needed):
                continue
            formats_available.append(
                {
                    "format": fmt["format"],
                    "filesize": fmt["filesize"],
                    "format_id": fmt["format_id"],
                    "ext": fmt["ext"],
                    "format_note": fmt["format_note"],
                    "yturl": link_norm,
                }
            )
        return formats_available, link_norm

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None) -> Tuple[str, str, str, str]:
        """
        Returns title, duration, thumbnail, id of the (query_type)-th suitable (<1h) result
        from a VideosSearch(query).
        """
        link_norm = sanitize_link(self.base_watch + link if videoid else link)
        try:
            vs = VideosSearch(link_norm, limit=10)
            raw_results = (await vs.next()).get("result", [])

            filtered: List[Dict[str, Any]] = []
            for item in raw_results:
                dur_txt = item.get("duration", "0:00")
                dur_secs = duration_to_secs_hard(dur_txt) or 0
                if dur_secs <= 3600:
                    filtered.append(item)

            if not filtered or query_type >= len(filtered):
                raise ValueError("No suitable videos found within duration limit")

            sel = filtered[query_type]
            return (
                sel["title"],
                sel["duration"],
                sel["thumbnails"][0]["url"].split("?", 1)[0],
                sel["id"],
            )
        except Exception as e:
            logger.error(f"slider(): {e}")
            raise ValueError("Failed to fetch video details")

    # ------------------------------
    # Download logic
    # ------------------------------
    async def download(
        self,
        link: str,
        mystic,  # kept for compat, not used
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Tuple[Optional[str], bool]:
        """
        High-level download entry point.
        Returns (filepath, direct)
        - filepath: str path to downloaded file or None on failure
        - direct: bool True means: ready to stream/upload without extra processing
        Notes:
        * Uses external YTPROXY service for audio/video direct URLs when possible.
        * Falls back to yt_dlp for manual merge.
        """
        # figure out video id + canonical link
        if videoid:
            vid_id = link
            full_link = f"{self.base_watch}{link}"
        else:
            vid_id = None
            full_link = link

        loop = asyncio.get_running_loop()

        async def download_with_curl(url: str, filepath: str, headers: Dict[str, str]) -> Optional[str]:
            """Try fast curl-based download with headers + resume."""
            cmd = [
                "curl","-L",           # follow redirects
                "-C","-",              # resume
                "--retry","3",
                "--retry-delay","1",
                "--retry-max-time","600",
                "--connect-timeout","30",
                "--max-time","60",
                "--silent",
                "--show-error",
                "--fail",
            ]
            # headers
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
            cmd.extend(["-o", filepath, url])

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and os.path.exists(filepath):
                return filepath
            err_msg = stderr.decode(errors="ignore") if stderr else "unknown curl error"
            logger.error(f"download_with_curl(): failed: {err_msg}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return None

        async def download_with_requests_fallback(url: str, filepath: str, headers: Dict[str, str]) -> Optional[str]:
            """If curl path fails, stream via requests with retries."""
            session = create_session()
            try:
                r = session.get(url, headers=headers, stream=True, timeout=60)
                r.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return filepath
            except Exception as e:
                logger.error(f"download_with_requests_fallback(): {e}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
            finally:
                session.close()

        async def proxy_audio_download(vid: str) -> Optional[str]:
            if not YT_API_KEY:
                logger.error("proxy_audio_download(): missing YT_API_KEY in config")
                return None
            if not YTPROXY:
                logger.error("proxy_audio_download(): missing YTPROXY_URL in config")
                return None

            headers = {
                "x-api-key": str(YT_API_KEY),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            filepath = os.path.join("downloads", f"{vid}.mp3")
            if os.path.exists(filepath):
                return filepath

            session = create_session()
            try:
                resp = session.get(f"{YTPROXY}/info/{vid}", headers=headers, timeout=60)
                data = resp.json()
            except Exception as e:
                logger.error(f"proxy_audio_download(): bad response: {e}")
                session.close()
                return None
            finally:
                session.close()

            status = data.get("status")
            if status == "success":
                audio_url = data.get("audio_url")
                if not audio_url:
                    logger.error("proxy_audio_download(): no audio_url in success response")
                    return None
                # try curl -> requests
                result = await download_with_curl(audio_url, filepath, headers)
                if result:
                    return result
                return await download_with_requests_fallback(audio_url, filepath, headers)

            if status == "error":
                logger.error(f"proxy_audio_download(): API error: {data.get('message')}")
                return None

            logger.error("proxy_audio_download(): Could not fetch Backend / invalid status")
            return None

        async def proxy_video_download(vid: str) -> Optional[str]:
            if not YT_API_KEY:
                logger.error("proxy_video_download(): missing YT_API_KEY in config")
                return None
            if not YTPROXY:
                logger.error("proxy_video_download(): missing YTPROXY_URL in config")
                return None

            headers = {
                "x-api-key": str(YT_API_KEY),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            filepath = os.path.join("downloads", f"{vid}.mp4")
            if os.path.exists(filepath):
                return filepath

            session = create_session()
            try:
                resp = session.get(f"{YTPROXY}/info/{vid}", headers=headers, timeout=60)
                data = resp.json()
            except Exception as e:
                logger.error(f"proxy_video_download(): bad response: {e}")
                session.close()
                return None
            finally:
                session.close()

            status = data.get("status")
            if status == "success":
                video_url = data.get("video_url")
                if not video_url:
                    logger.error("proxy_video_download(): no video_url in success response")
                    return None
                # try curl -> requests
                result = await download_with_curl(video_url, filepath, headers)
                if result:
                    return result
                return await download_with_requests_fallback(video_url, filepath, headers)

            if status == "error":
                logger.error(f"proxy_video_download(): API error: {data.get('message')}")
                return None

            logger.error("proxy_video_download(): Could not fetch Backend / invalid status")
            return None

        def merge_video_audio_with_yt_dlp() -> Optional[str]:
            """
            Use yt-dlp with given format_id to download + merge best video+audio.
            Returns the final path (mp4) or None on failure.
            """
            if not (title and format_id):
                logger.error("merge_video_audio_with_yt_dlp(): missing title or format_id")
                return None
            final_base = os.path.join("downloads", str(title))
            ydl_opts = {
                "format": f"{format_id}+140",
                "outtmpl": final_base,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_txt_file(),
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            try:
                yt_dlp.YoutubeDL(ydl_opts).download([full_link])
            except Exception as e:
                logger.error(f"merge_video_audio_with_yt_dlp(): {e}")
                return None
            return final_base + ".mp4"

        def extract_audio_with_yt_dlp() -> Optional[str]:
            """
            Use yt-dlp to grab audio-only, convert to mp3.
            Returns final path or None.
            """
            if not (title and format_id):
                logger.error("extract_audio_with_yt_dlp(): missing title or format_id")
                return None
            tmpl = os.path.join("downloads", f"{title}.%(ext)s")
            ydl_opts = {
                "format": format_id,
                "outtmpl": tmpl,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_txt_file(),
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            try:
                yt_dlp.YoutubeDL(ydl_opts).download([full_link])
            except Exception as e:
                logger.error(f"extract_audio_with_yt_dlp(): {e}")
                return None
            return os.path.join("downloads", f"{title}.mp3")

        # -------------------------------------------------
        # Decision tree
        # -------------------------------------------------
        # 1. Manual merge path (user asked for specific format)
        if songvideo:
            # user wants final mp4 for given format_id
            out_path = await loop.run_in_executor(None, merge_video_audio_with_yt_dlp)
            return out_path, True

        if songaudio:
            # user wants final mp3 for given format_id
            out_path = await loop.run_in_executor(None, extract_audio_with_yt_dlp)
            return out_path, True

        # 2. Direct proxy grab (preferred path for bot playback)
        if video:
            # need video (mp4)
            final_file = await proxy_video_download(vid_id or "")
            return final_file, True
        else:
            # need audio (mp3)
            final_file = await proxy_audio_download(vid_id or "")
            return final_file, True
