"""YouTube localization parameters utils module.

hl (Host Language): Controls the interface language of YouTube. 
This determines what language the UI elements, buttons, menus, and text 
are displayed in. 
Example: tje hl=en shows the interface in English, hl=es in Spanish, etc.

gl (Geographic Location): Controls the regional content and 
recommendations. This affects which videos are shown, trending content, 
and content availability based on geographic restrictions. For example, 
gl=US shows content as if you're browsing from the United States, 
gl=GB from Great Britain, etc.
Example: a URL like https://youtube.com/watch?v=xyz&hl=en&gl=US would:
Display the YouTube interface in English (hl=en)
Show content/recommendations as if browsing from the US (gl=US)

These parameters are useful for:
- Ensuring consistent screenshots regardless of user location
- Testing how content appears in different regions
- Accessing region-specific content or avoiding geo-restrictions
"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import config


def with_yt_locale(url: str) -> str:
    """Add YouTube locale parameters to URL if 
    config.USE_YOUTUBE_LOCALE is enabled.
    """
    if not config.USE_YOUTUBE_LOCALE:
        return url
    try:
        parts = urlsplit(url)
        query_items = parse_qsl(parts.query, keep_blank_values=True)
        keys = {k for k, _ in query_items}
        if "hl" not in keys:
            query_items.append(("hl", config.YOUTUBE_HL))
        if "gl" not in keys:
            query_items.append(("gl", config.YOUTUBE_GL))
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(query_items),
                parts.fragment,
            )
        )
    except Exception:
        return url
