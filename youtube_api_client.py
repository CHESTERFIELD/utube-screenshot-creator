import datetime
import json
import logging
import threading
import urllib.parse
import urllib.request
from typing import Optional

from googleapiclient.discovery import build

import config

logger = logging.getLogger(__name__)

# Thread-local storage so each thread gets its own HTTP connection.
_thread_local = threading.local()


def _get_youtube_service():
    """Returns a per-thread YouTube Data API v3 service.

    Each thread owns its own service (and underlying HTTP connection)
    so concurrent calls from a ThreadPool do not fight over a single
    connection pool.
    """
    svc = getattr(_thread_local, "youtube_service", None)
    if svc is None:
        key = getattr(config, "YOUTUBE_API_KEY", None)
        if not key:
            raise ValueError(
                "YOUTUBE_API_KEY environment variable is not set. "
                "Get one at https://console.cloud.google.com/apis/credentials"
            )
        svc = build("youtube", "v3", developerKey=key)
        _thread_local.youtube_service = svc
    return svc


def _extract_video_id(url: str) -> str:
    """Extract the video ID from various YouTube URL formats."""
    parsed = urllib.parse.urlparse(url)

    # https://youtu.be/<id>
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/").split("/")[0]

    # https://www.youtube.com/watch?v=<id>
    qs = urllib.parse.parse_qs(parsed.query)
    if "v" in qs:
        return qs["v"][0]

    # https://www.youtube.com/embed/<id>  or /v/<id> or /shorts/<id>
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] in ("embed", "v", "shorts"):
        return parts[1]

    raise ValueError(f"Cannot extract video ID from URL: {url}")


def _extract_channel_identifier(url: str) -> tuple[str, str]:
    """Extract channel identifier and its type from a URL.

    Returns (param_name, value) where param_name is one of:
    - 'id'           for /channel/<channel_id>
    - 'handle'       for /@handle (requires search API)
    - 'forUsername'  for /user/<username> or /c/<custom>
    """
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")

    if not parts or not parts[0]:
        raise ValueError(f"Cannot extract channel identifier from URL: {url}")

    first = parts[0]

    # /channel/UC...
    if first == "channel" and len(parts) >= 2:
        return ("id", parts[1])

    # /@handle
    if first.startswith("@"):
        return ("handle", first)

    # /user/<username>
    if first == "user" and len(parts) >= 2:
        return ("forUsername", parts[1])

    # /c/<custom>
    if first == "c" and len(parts) >= 2:
        return ("forUsername", parts[1])

    # bare handle e.g. youtube.com/TIMTIN -> try handle with @
    return ("handle", f"@{first}")


class UtubeApiClient:
    """YouTube client using the YouTube Data API v3 (GET requests only).

    Follows the same interface as UtubeClient so it can be used as a
    drop-in replacement.
    """

    def __init__(self, video_url: str) -> None:
        self._video_url = video_url
        self._video_id = _extract_video_id(video_url)
        self._snippet: Optional[dict] = None
        self._statistics: Optional[dict] = None

        self._fetch()

    def _fetch(self) -> None:
        """Fetch video details from the API (single call)."""
        if self._snippet is not None:
            return
        yt = _get_youtube_service()
        params = {
            "part": "snippet,statistics",
            "id": self._video_id,
        }
        if config.USE_YOUTUBE_LOCALE:
            params["hl"] = config.YOUTUBE_HL
        response = yt.videos().list(**params).execute()
        items = response.get("items", [])
        if not items:
            raise ValueError(
                f"Video not found via API: {self._video_url} "
                f"(id={self._video_id})"
            )
        self._snippet = items[0]["snippet"]
        self._statistics = items[0].get("statistics", {})

    def get_views_count(self) -> int:
        """Returns current views count."""
        return int(self._statistics.get("viewCount", 0))

    def get_publish_date(self) -> datetime.datetime:
        """Returns datetime.datetime of video publish date."""
        # publishedAt is ISO 8601: "2023-01-15T12:00:00Z"
        raw = self._snippet["publishedAt"]
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        # Return naive UTC datetime to match pytube behaviour
        return dt.replace(tzinfo=None)

    def get_title(self) -> str:
        """Returns video title."""
        return self._snippet["title"]


def fetch_videos_batch(video_urls: list[str]) -> dict[str, "UtubeApiClient"]:
    """Fetch multiple videos in batch using the YouTube Data API v3.

    The API supports up to 50 video IDs per request.  This function
    transparently chunks the input list and returns a dict mapping
    each original *video_url* to a fully-initialised UtubeApiClient
    (with snippet + statistics already populated).

    Videos that are not found by the API are silently skipped.
    """
    BATCH_SIZE = 50

    url_to_id: dict[str, str] = {}
    id_to_urls: dict[str, list[str]] = {}
    for url in video_urls:
        vid = _extract_video_id(url)
        url_to_id[url] = vid
        id_to_urls.setdefault(vid, []).append(url)

    unique_ids = list(id_to_urls.keys())
    id_to_item: dict[str, dict] = {}

    yt = _get_youtube_service()
    for i in range(0, len(unique_ids), BATCH_SIZE):
        chunk = unique_ids[i : i + BATCH_SIZE]
        params: dict = {
            "part": "snippet,statistics",
            "id": ",".join(chunk),
        }
        if config.USE_YOUTUBE_LOCALE:
            params["hl"] = config.YOUTUBE_HL
        response = yt.videos().list(**params).execute()
        for item in response.get("items", []):
            id_to_item[item["id"]] = item

    result: dict[str, UtubeApiClient] = {}
    for url in video_urls:
        vid = url_to_id[url]
        item = id_to_item.get(vid)
        if item is None:
            logger.warning("Video not found in batch response: %s (id=%s)", url, vid)
            continue
        client = object.__new__(UtubeApiClient)
        client._video_url = url
        client._video_id = vid
        client._snippet = item["snippet"]
        client._statistics = item.get("statistics", {})
        result[url] = client

    logger.info(
        "Batch API: fetched %d/%d videos in %d request(s)",
        len(result),
        len(video_urls),
        (len(unique_ids) + BATCH_SIZE - 1) // BATCH_SIZE,
    )
    return result


def get_channel_name(channel_link: str) -> str:
    """Returns channel's name using the YouTube Data API v3."""
    parsed = urllib.parse.urlparse(channel_link)
    # Build a full URL if only a path-like string was given
    if not parsed.scheme:
        channel_link = f"{config.YOUTUBE_URL}/{channel_link.lstrip('/')}"

    param_name, value = _extract_channel_identifier(channel_link)
    yt = _get_youtube_service()
    
    # For handles (@username), use forHandle parameter or search API based on config
    if param_name == "handle":
        if config.USE_FORHANDLE_API:
            # Use forHandle parameter via direct HTTP request
            # (the client library may not support forHandle in older versions)
            handle = urllib.parse.quote(value.lstrip("@"))
            api_url = (
                f"https://www.googleapis.com/youtube/v3/channels"
                f"?part=snippet"
                f"&forHandle={handle}"
                f"&key={config.YOUTUBE_API_KEY}"
            )
            with urllib.request.urlopen(api_url) as resp:
                response = json.loads(resp.read())
        else:
            # Fallback to search API (legacy method)
            # For handles (@username), we need to use the search API to find the channel ID first
            search_response = yt.search().list(
                part="snippet",
                q=value,
                type="channel",
                maxResults=1
            ).execute()
            search_items = search_response.get("items", [])
            if not search_items:
                raise ValueError(f"Channel not found via API: {channel_link}")
            channel_id = search_items[0]["snippet"]["channelId"]
            response = yt.channels().list(
                part="snippet",
                id=channel_id
            ).execute()
    else:
        # For id or forUsername, use channels().list() directly
        response = yt.channels().list(
            part="snippet",
            **{param_name: value},
        ).execute()
    
    items = response.get("items", [])
    if not items:
        # Fallback to search API for /c/ custom URLs (forUsername doesn't work for them)
        logger.warning(
            "Channel not found with %s=%s, trying search API fallback: %s",
            param_name, value, channel_link
        )
        search_response = yt.search().list(
            part="snippet",
            q=value,
            type="channel",
            maxResults=1
        ).execute()
        search_items = search_response.get("items", [])
        if not search_items:
            raise ValueError(f"Channel not found via API: {channel_link}")
        channel_id = search_items[0]["snippet"]["channelId"]
        response = yt.channels().list(
            part="snippet",
            id=channel_id
        ).execute()
        items = response.get("items", [])
        if not items:
            raise ValueError(f"Channel not found via API: {channel_link}")
    return items[0]["snippet"]["title"]
