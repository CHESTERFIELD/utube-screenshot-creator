import datetime
import logging
import os
import time
from io import BytesIO
from PIL import Image, ImageEnhance
from multiprocessing.pool import ThreadPool as Pool
from typing import Optional, Tuple

import selenium.webdriver.remote.webelement
from selenium import webdriver

import config
from telegram_client import (
    send_picture_telegram_bot, send_message_telegram_bot
)
from youtube_client import UtubeClient, get_channel_name


ACCEPT_ALL_UA = "Прийняти усі"
ACCEPT_ALL_EN = "Accept all"


def parse_video_link_from_weblement(webelement):
    """Parses href property from filtered video web element."""
    try:
        title_link_element = webelement.find_element_by_id("video-title-link")
    except Exception as err:
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
            return utube.get_publish_date()
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


def fetch_and_filter_element(element) -> Optional[Tuple[
        str, str, selenium.webdriver.remote.webelement.WebElement]]:
    """Compute selenium.WebElement vid_info data and returns required data
    covered to the tuple if it under conditions or None.
    """
    video_link = parse_video_link_from_weblement(element)

    attempt = 0
    while True:
        try:
            attempt += 1

            logging.info("Attempt %s to find data for %s\n",
                         attempt, video_link)

            utube = UtubeClient(video_link)
            publish_date = utube.get_publish_date()
            views = utube.get_views_count()
            title = utube.get_title()

            logging.info("Publish date: %s\nViews: %s\nTitle: %s\n",
                         publish_date, views, title)

            # publish date less then 14 days and has 200k+ views
            if config.FIFTEEN_DAYS_AGO < publish_date \
                    and views > config.CLAUSE_200K:
                return title, video_link, element
            # publish date less then 45 days and has 300k+ views
            elif config.FORTY_FIVE_DAYS_AGO < publish_date < config.FIFTEEN_DAYS_AGO \
                    and views > config.CLAUSE_300K:
                return title, video_link, element
            # if publish date over then 45 days just stop on it
            elif config.FORTY_FIVE_DAYS_AGO > utube.get_publish_date():
                logging.info("Very old element is found")

            # exit from while loop
            return None
        except Exception as err:
            if attempt > 10:
                logging.error(err, "Failed to get video info for '%s'",
                              video_link)
                raise


def main():
    links = input(f"Input youtube channel links (example: "
                  f"{config.TIM_TIM_URL},{config.TIM_TIM_URL})\n")
    if not links:
        links = config.TIM_TIM_URL

    # remove whitespaces
    links = links.strip()

    channel_links = links.split(',')
    channels = ((get_channel_name(channel_link), channel_link)
                for channel_link in channel_links)

    # create a webdriver instance
    real_final = False
    driver = webdriver.Chrome(config.CHROMEDRIVER_PATH)
    last_processed_channel_link = None
    try:
        for channel_name, channel_link in channels:
            last_processed_channel_link = channel_link
            # navigate to the webpage with the desired element
            driver.get(f"{channel_link}/videos")

            # Click the button to skip cookie banner (cold start only)
            try:
                label = ACCEPT_ALL_UA if config.OS_PRIMARY_LANGUAGE == "UA" \
                    else ACCEPT_ALL_EN

                agree_button = driver.find_element_by_xpath(
                    f"//button[@aria-label='{label}']")
                agree_button.click()
            except Exception as err:
                logging.warning("Unable to find \"Accept all\" button."
                                "Error occurred: %s", err)

            # TODO: do we really need this sleep call here?
            # sleep 3 seconds to wait when page and previews pictures loaded
            time.sleep(3)

            skip_second_page = False
            first_page_elements = driver.find_elements_by_tag_name(
                "ytd-rich-item-renderer")
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
            else:
                screenshots_elements = first_page_elements

            # loading second page is not required for development
            if config.DEV_MODE:
                skip_second_page = True
                screenshots_elements = screenshots_elements[:5]

            if not skip_second_page:
                # parse the element of interest
                if load_second_page(first_page_elements[-1]):
                    # scroll to the end of the page to call JS script to
                    # download next 30 videos for client (driver)
                    app = driver.find_element_by_tag_name("ytd-app")
                    driver.execute_script(
                        f"window.scrollTo(0, {app.size['height']});")

                    # TODO: do we really need this sleep call here?
                    # sleep 3 seconds to wait when page and previews pictures loaded
                    time.sleep(3)

                    screenshots_elements = driver.find_elements_by_tag_name(
                        "ytd-rich-item-renderer")
                    # check if elements on first page should be sliced 45/60
                    if not is_check_datetime_older_than_video_publish_date(
                            screenshots_elements[45], config.FORTY_FIVE_DAYS_AGO):
                        screenshots_elements = screenshots_elements[:45]
                else:
                    screenshots_elements = driver.find_elements_by_tag_name(
                        "ytd-rich-item-renderer")

            logging.info("Found %s screenshot elements",
                         len(screenshots_elements))

            # Create a pool of worker processes
            with Pool(processes=os.cpu_count()-1) as pool:
                # Use the map method to call the fetch_and_filter_element
                # function for each element in parallel
                filtered_screenshot_elements = pool.map(
                    fetch_and_filter_element, screenshots_elements)

            # remove None items
            filtered_screenshot_elements = [
                el for el in filtered_screenshot_elements if el]

            logging.info("Found %s filtered screenshot elements",
                         len(filtered_screenshot_elements))

            send_message_telegram_bot(channel_name)
            # take a screenshot of the element and save it to a file and send
            for title, video_link, el in filtered_screenshot_elements:
                # remove slashes to avoid wrong path error
                title_without_slash = title.replace("/", "")
                screenshot_path = os.path.join(
                    config.SCREENSHOTS_PATH, f"{title_without_slash}.png")

                # scroll viewable part of driver window to the element Y point
                # to be able to take a screenshot in a full size
                driver.execute_script(
                    f"window.scrollTo(0, {el.location['y']-el.size['height']});")

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
    except Exception as err:
        logging.error("\nERROR\nERROR\nERROR\nERROR\nERROR\n%s", err)
        logging.info("Last processed channel: %s", last_processed_channel_link)
    finally:
        if real_final:
            logging.info("\nSUCCESS\nSUCCESS\nSUCCESS\nSUCCESS\nSUCCESS")
        if driver:
            driver.quit()


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN env var is not set")

    if not config.SCREENSHOTS_PATH:
        raise ValueError("SCREENSHOTS_PATH env var is not set")

    if not config.CHAT_ID:
        raise ValueError("CHAT_ID env var is not set")

    if not config.CHROMEDRIVER_PATH:
        raise ValueError("CHROMEDRIVER_PATH env var is not set")

    start = time.time()
    main()
    logging.info("Finishing parse process in %f seconds", time.time() - start)
