import datetime
import os

import requests
from PIL import Image, ImageDraw
from pytube import YouTube, Channel
import re
from slugify import slugify

import config


class UtubeClient(YouTube):

    """Follow YouTube class, but implemented to have custom client."""

    def __init__(self, *args, **kwargs) -> None:
        # YouTube("https://www.youtube.com/watch?v=PaLTbiwPTpk")
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


def has_cyrillic(text: str):
    """Checks received string on cyrillic symbols."""
    return bool(re.search('[а-яА-Я]', text))


def main():
    # Instantiate a YouTube object for the video you want to download
    yt = YouTube("https://www.youtube.com/watch?v=PaLTbiwPTpk")

    # Get the preview image URL
    preview_url = yt.thumbnail_url

    # Download the preview image and open it with Pillow
    preview_image = Image.open(requests.get(preview_url, stream=True).raw)

    # Create a new image with the same dimensions as the preview image
    width, height = preview_image.size
    width = width * 2
    height = height * 2
    new_image = Image.new('RGB', (width, height), (255, 255, 255))

    # Paste the preview image onto the new image
    new_image.paste(preview_image)

    # Add details to the new image
    draw = ImageDraw.Draw(new_image)
    title = "test"
    draw.text((10, height + 2000), title, fill=(0, 255, 0))

    author = f"Author: {yt.author}"
    draw.text((10, height + 150), author,  fill=(0, 255, 0))

    views = f"Views: {yt.views}"
    draw.text((10, height + 50), views, fill=(0, 255, 0))

    if has_cyrillic(title):
        title = slugify(title)
    image_path = os.path.join(config.SCREENSHOTS_PATH, f'{title}.jpg')

    # Save the new image
    new_image.save(image_path)


if __name__ == "__main__":
    main()
