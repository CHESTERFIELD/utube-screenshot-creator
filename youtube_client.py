import datetime
from pytube import YouTube, Channel
from pytube import request

import config


class UtubeClient(YouTube):
    """Follow YouTube class, but implemented to have custom client."""

    def __init__(self, *args, **kwargs) -> None:
        try:
            request.default_headers["Accept-Language"] = config.YOUTUBE_ACCEPT_LANGUAGES
        except Exception:
            pass
        super().__init__(*args, **kwargs)

    def get_views_count(self) -> int:
        """Returns current views count."""
        return self.views

    def get_publish_date(self) -> datetime.datetime:
        """Returns datetime.datetime of video publish date."""
        return self.publish_date

    def get_title(self) -> str:
        """Returns video title."""
        return self.title


def get_channel_name(channel_link: str) -> str:
    """Returns channel's name."""
    return Channel(channel_link).channel_name
