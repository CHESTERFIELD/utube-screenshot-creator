import datetime
import logging
import os
import ssl
import time
from io import BytesIO
from PIL import Image, ImageEnhance
from multiprocessing.pool import ThreadPool as Pool
from typing import Optional, Tuple

import certifi
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import config
from telegram_client import (
    send_picture_telegram_bot, send_message_telegram_bot
)

# Depends on config.USE_YOUTUBE_API control which client to use
# putube OR google API + key to fetch videos data
if config.USE_YOUTUBE_API:
    from youtube_api_client import (
        UtubeApiClient as UtubeClient, 
        get_channel_name, 
        fetch_videos_batch
    )
else:
    from youtube_client import UtubeClient, get_channel_name

from youtube_navigation_utils import (
    handle_cookie_banner, navigate_to_videos_page
)

from youtube_find_elements_utils import (
    find_screenshot_elements, find_element_by_tag_name, 
    find_thumbnail_img
)

from youtube_localization_utils import (
    with_yt_locale
)


def _wait_for_video_cards(driver: webdriver.Chrome, timeout_seconds: int = 20) -> None:
    """Wait for video cards to be loaded."""
    _wait_for_video_cards_min_count(driver, min_count=1, timeout_seconds=timeout_seconds)


def _wait_for_video_cards_min_count(
    driver: webdriver.Chrome,
    min_count: int,
    timeout_seconds: int = 20,
) -> None:
    """Wait for video cards to be loaded."""
    WebDriverWait(driver, timeout_seconds).until(
        lambda d: len(find_screenshot_elements(d)) >= min_count
    )


def _is_img_loaded(driver: webdriver.Chrome, img_el) -> bool:
    """Check if image is loaded."""
    try:
        return bool(driver.execute_script(
            """
            const img = arguments[0];
            if (!img) return false;
            const src = img.currentSrc || img.src || '';
            if (!src) return false;
            if (src.startsWith('data:')) return false;
            return img.complete === true && img.naturalWidth > 0;
            """,
            img_el,
        ))
    except Exception:
        return False


def _wait_for_thumbnail_loaded(
    driver: webdriver.Chrome,
    video_card_el,
    timeout_seconds: int = 15,
) -> None:
    """Wait for thumbnail to be loaded."""
    img_el = find_thumbnail_img(video_card_el)
    if not img_el:
        return
    WebDriverWait(driver, timeout_seconds).until(lambda d: _is_img_loaded(d, img_el))


def parse_video_link_from_weblement(webelement):
    """Parses href property from filtered video web element."""
    try:
        title_link_element = webelement.find_element(By.ID, "video-title-link")
    except Exception as err:
        try:
            title_link_element = webelement.find_element(By.CLASS_NAME, "ytLockupViewModelContentImage")
        except Exception:
            logging.error(err)
            raise
    return title_link_element.get_property('href')


def get_video_publish_date(video_link: str) -> Optional[datetime.datetime]:
    """Fetches video's publish date info for passed argument."""
    attempt = 0
    while True:
        try:
            attempt += 1
            utube = UtubeClient(video_link)
            publish_date = utube.get_publish_date()
            if attempt < 10:
                if not publish_date:
                    time.sleep(1)
                    continue
                return publish_date
            else:
                raise ValueError(f"Failed to get video info for '{video_link}'")
        except Exception as err:
            if attempt > 10:
                logging.error(err, "Failed to get video info for '%s'",
                              video_link)
                raise


def load_second_page(last_video_element) -> bool:
    """Check if page should be scrolled down to notify browser to load next
    30 videos to be parsed.
    """
    logging.info("Checking if the second page have to be loaded")
    return is_check_datetime_older_than_video_publish_date(
        last_video_element, config.FORTY_FIVE_DAYS_AGO)


def is_check_datetime_older_than_video_publish_date(
        video_webelement, check_datetime: datetime.datetime) -> bool:
    """Checking if video is older than check_datetime argument."""
    link = parse_video_link_from_weblement(video_webelement)
    publish_date = get_video_publish_date(link)
    if check_datetime < publish_date:
        return True
    return False


def fetch_and_filter_video(video_link: str) -> Optional[Tuple[str, str]]:
    """Fetch video info via API and return (title, video_link) if it
    meets the view/date thresholds, or None otherwise.

    This function is safe to call from worker threads because it does
    NOT touch any Selenium objects.
    """
    attempt = 0
    while True:
        try:
            attempt += 1
            logging.info("Attempt %s to find data for %s\n",
                         attempt, video_link)

            utube = UtubeClient(with_yt_locale(video_link))
            publish_date = utube.get_publish_date()
            views = utube.get_views_count()
            title = utube.get_title()

            logging.info("Publish date: %s\nViews: %s\nTitle: %s\n",
                         publish_date, views, title)
            
            if config.SKIP_FILTERING_BY_DATE:
                return title, video_link

            # publish date less then 14 days and has 200k+ views
            if config.FIFTEEN_DAYS_AGO < publish_date \
                    and views > config.CLAUSE_200K:
                return title, video_link
            # publish date less then 45 days and has 300k+ views
            elif config.FORTY_FIVE_DAYS_AGO < publish_date < config.FIFTEEN_DAYS_AGO \
                    and views > config.CLAUSE_300K:
                return title, video_link
            # if publish date over then 45 days just stop on it
            elif config.FORTY_FIVE_DAYS_AGO > utube.get_publish_date():
                logging.info("Very old element is found")

            # exit from while loop
            return None
        except Exception as err:
            if attempt >= 10:
                logging.error("Failed to get video info for %s: %s",
                              video_link, err)
                raise


def _filter_video(utube, video_link: str) -> Optional[Tuple[str, str]]:
    """Apply view/date filtering to a pre-fetched UtubeApiClient instance.

    Returns (title, video_link) if the video passes thresholds, else None.
    """
    publish_date = utube.get_publish_date()
    views = utube.get_views_count()
    title = utube.get_title()

    logging.info("Publish date: %s\nViews: %s\nTitle: %s\n",
                 publish_date, views, title)

    if config.SKIP_FILTERING_BY_DATE:
        return title, video_link

    if config.FIFTEEN_DAYS_AGO < publish_date \
            and views > config.CLAUSE_200K:
        return title, video_link
    elif config.FORTY_FIVE_DAYS_AGO < publish_date < config.FIFTEEN_DAYS_AGO \
            and views > config.CLAUSE_300K:
        return title, video_link
    elif config.FORTY_FIVE_DAYS_AGO > publish_date:
        logging.info("Very old element is found")

    return None


def fetch_and_filter_videos_batch(
    video_links: list[str],
) -> list[Tuple[str, str]]:
    """Fetch all videos in batch and apply view/date filtering.

    Uses the YouTube Data API v3 batch endpoint (up to 50 IDs per
    request) to drastically reduce the number of API calls.
    """
    localized_links = [with_yt_locale(link) for link in video_links]
    clients = fetch_videos_batch(localized_links)

    results: list[Tuple[str, str]] = []
    for link, localized in zip(video_links, localized_links):
        utube = clients.get(localized)
        if utube is None:
            logging.warning("Skipping %s – not found in batch response", link)
            continue
        res = _filter_video(utube, link)
        if res is not None:
            results.append(res)
    return results


def run_app(channel_links: list[str]):
    channels = ((get_channel_name(channel_link), channel_link)
                for channel_link in channel_links)

    # determine if app is actually finished and ready to close the
    # browser page
    real_final = False

    # create a webdriver instance
    options = Options()
    if config.USE_YOUTUBE_LOCALE:
        options.add_argument(f"--lang={config.CHROME_LANG}")
        options.add_experimental_option(
            "prefs",
            {"intl.accept_languages": config.YOUTUBE_ACCEPT_LANGUAGES},
        )
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(config.CHROMEDRIVER_PATH, options=options)
    
    if config.TEST_NETWORK_CONDITIONS:
        driver.execute_cdp_cmd("Network.enable", {})
        # Example: "Slow 3G"-ish
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": 20,                 # ms RTT
            "downloadThroughput": 2500 * 1024 / 8,  # bytes/sec (e.g. 400 kbps)
            "uploadThroughput":   2500 * 1024 / 8,  # bytes/sec (e.g. 200 kbps)
            "connectionType": "cellular3g",
        })

    banner_closed = False
    last_processed_channel_link = None
    try:
        for channel_name, channel_link in channels:
            last_processed_channel_link = channel_link

            # navigate to the webpage with the desired element
            driver.get(with_yt_locale(f"{channel_link}/videos"))

            if not banner_closed:
                handle_cookie_banner(driver)
                banner_closed = True

            _wait_for_video_cards(driver)

            if config.CUSTOM_WORKAROUND_ENABLED:
                navigate_to_videos_page(driver)

            skip_second_page = False
            first_page_elements = find_screenshot_elements(driver)
            
            # set all, than check if filtering required
            screenshots_elements = first_page_elements
            if not config.SKIP_FILTERING_BY_DATE:
                # check if elements on first page should be sliced 15/30
                if not is_check_datetime_older_than_video_publish_date(
                        first_page_elements[14], config.FORTY_FIVE_DAYS_AGO):
                    screenshots_elements = first_page_elements[:15]
                    # check if elements on first page should be sliced 8/30
                    if not is_check_datetime_older_than_video_publish_date(
                            screenshots_elements[7], config.FORTY_FIVE_DAYS_AGO):
                        screenshots_elements = screenshots_elements[:8]
                        # check if elements on first page should be sliced 4/30
                        if not is_check_datetime_older_than_video_publish_date(
                                screenshots_elements[3], config.FORTY_FIVE_DAYS_AGO):
                            screenshots_elements = screenshots_elements[:4]
                    skip_second_page = True
                
            if config.SKIP_SECOND_PAGE:
                skip_second_page = True

            if not skip_second_page:
                # parse the element of interest
                if load_second_page(first_page_elements[-1]):
                    # scroll to the end of the page to call JS script to
                    # download next 30 videos for client (driver)
                    prev_count = len(find_screenshot_elements(driver))
                    driver.execute_script(
                        f"window.scrollTo(0, {find_element_by_tag_name(driver, 'ytd-app').size['height']});"
                    )

                    _wait_for_video_cards_min_count(driver, min_count=prev_count + 1)

                    screenshots_elements = find_screenshot_elements(driver)
                    if not config.SKIP_FILTERING_BY_DATE:
                        # check if elements on first page should be sliced 45/60
                        if not is_check_datetime_older_than_video_publish_date(
                                screenshots_elements[45], config.FORTY_FIVE_DAYS_AGO):  
                            screenshots_elements = screenshots_elements[:45]
                else:
                    screenshots_elements = find_screenshot_elements(driver)

            logging.info("Found %s screenshot elements",len(screenshots_elements))

            # Extract video links on the main thread (Selenium is
            # NOT thread-safe so WebElements must not be touched by
            # worker threads).
            video_links = []
            link_to_element = {}
            for el in screenshots_elements:
                try:
                    link = parse_video_link_from_weblement(el)
                    video_links.append(link)
                    link_to_element[link] = el
                except Exception:
                    logging.warning("Skipping element could not extract link")

            if config.USE_YOUTUBE_API and config.USE_BATCH_API:
                filtered_results = fetch_and_filter_videos_batch(
                    video_links)
            else:
                # expecting youtube API will not return 429 error
                # so we can use all available CPU cores to make
                # request to collect information about videos
                if config.USE_YOUTUBE_API:
                    process_number = int(os.cpu_count()-1)
                else:
                    process_number = 1

                # Create a pool of worker threads – only plain strings
                # are sent in; no Selenium objects cross thread boundaries.
                with Pool(processes=process_number) as pool:
                    filtered_results = pool.map(
                        fetch_and_filter_video, video_links)

                # remove NoneType items for filtered out videos
                filtered_results = [
                    res for res in filtered_results if res]

            logging.info("Found %s filtered screenshot elements",
                         len(filtered_results))

            send_message_telegram_bot(f"{channel_name}\n{channel_link}")
            # take a screenshot of the element and save it to a file and send
            for title, video_link in filtered_results:
                el = link_to_element[video_link]
                # remove slashes to avoid wrong path error
                title_without_slash = title.replace("/", "")
                screenshot_path = os.path.join(
                    config.SCREENSHOTS_PATH, f"{title_without_slash}.png")

                # scroll viewable part of driver window to the element Y point
                # to be able to take a screenshot in a full size
                driver.execute_script(
                    f"window.scrollTo(0, {el.location['y']-el.size['height']});")

                try:
                    _wait_for_thumbnail_loaded(driver, el)
                except TimeoutException:
                    logging.warning("Thumbnail did not load in time for %s", video_link)

                # code below enhance photo saturation
                # (colours to be more brightness)
                screenshot_as_png = el.screenshot_as_png
                # convert the screenshot to a PIL image object
                img = Image.open(BytesIO(screenshot_as_png))
                converter = ImageEnhance.Color(img)
                img = converter.enhance(1.5)
                # save the screenshot
                img.save(screenshot_path)
                # send screenshot to the
                send_picture_telegram_bot(screenshot_path, video_link)

        real_final = True
    except Exception:
        logging.exception("ERROR\n" * 5)
        logging.info("Last processed channel: %s", last_processed_channel_link)
    finally:
        if real_final:
            logging.info("SUCCESS\n" * 5)
        
        if not config.DEV_MODE:
            logging.info("Closing browser...")
            if driver:
                driver.quit()
        else:
            logging.info(
                "DEV_MODE is enabled, browser has not been closed "
                "for debugging purposes"
            )
            import ipdb
            ipdb.set_trace()
            
    
def main():
    """Entrypoint function to run the application."""
    # validation for required environment variables
    required_vars = [config.BOT_TOKEN, config.SCREENSHOTS_PATH, 
                     config.CHAT_ID, config.CHROMEDRIVER_PATH]
    if not all(required_vars):
        missing = [name for name, value in zip(
            ["BOT_TOKEN", "SCREENSHOTS_PATH", "CHAT_ID", "CHROMEDRIVER_PATH"], 
            required_vars) if not value]
        raise ValueError(f"Some required environment variables are "
                         f"not set: {', '.join(missing)}")

    # request youtube channel links as an input
    links = input(f"Input youtube channel links (example: "
                  f"{config.TIM_TIM_URL},{config.TIM_TIM_URL})\n")
    if not links:
        links = config.TIM_TIM_URL
        
    # remove whitespaces
    links = links.strip()

    # split string into list of links
    channel_links = links.split(',')
    
    # start parsing application
    start = time.time()
    run_app(channel_links)
    logging.info("Process finished in %f seconds", time.time() - start)


def _configure_ssl() -> None:
    """Configure SSL."""
    cafile = None
    try:
        cafile = certifi.where()
    except Exception:
        return

    if cafile:
        os.environ.setdefault("SSL_CERT_FILE", cafile)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", cafile)
        try:
            ssl._create_default_https_context = (
                lambda *args, **kwargs: ssl.create_default_context(cafile=cafile)
            )
        except Exception:
            return


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    _configure_ssl()

    main()
