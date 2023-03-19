import logging
import time
from multiprocessing.dummy import Pool
from typing import Optional, Tuple

import ipdb
import selenium.webdriver.remote.webelement
from selenium import webdriver
from selenium.webdriver import ActionChains

import config
from telegram_client import send_picture_telegram_bot, \
    send_message_telegram_bot
from youtube_client import UtubeClient, get_channel_name


class TelegramSendPictureFailedError(Exception):
    pass


class TelegramSendMessageFailedError(Exception):
    pass


def fetch_and_filter_element(element) -> Optional[Tuple[
        str, str, selenium.webdriver.remote.webelement.WebElement]]:
    title_link_element = element.find_element_by_id("video-title-link")
    direct_video_link = title_link_element.get_property('href')

    attempt = 0
    while True:
        try:
            attempt += 1
            utube = UtubeClient(direct_video_link)
            publish_date = utube.get_publish_date()
            views = utube.get_views_count()
            title = utube.get_title()

            logging.info("Attempt %s to find data for %s link: \n"
                         "Publish date: %s \nViews: %s \nTitle: %s \n",
                         attempt, direct_video_link, publish_date,
                         views, title)

            # publish date less then 14 days and has 200k+ views
            if config.FIFTEEN_DAYS_AGO < publish_date \
                    and views > config.CLAUSE_100K:
                return title, direct_video_link, element
            # publish date less then 45 days and has 300k+ views
            elif config.FORTY_FIVE_DAYS_AGO < publish_date < config.FIFTEEN_DAYS_AGO \
                    and views > config.CLAUSE_300K:
                return title, direct_video_link, element
            # if publish date over then 45 days just stop on it
            elif config.FORTY_FIVE_DAYS_AGO > utube.get_publish_date():
                logging.info("Very old element is found")

            # exit from while loop
            return None
        except Exception as err:
            if attempt > 3:
                logging.error(err, "Failed to get video info for '%s'",
                              direct_video_link)
                raise


def main():
    links = input(f"Input youtube channel links (example: "
                  f"{config.TIM_TIM_URL},{config.TIM_TIM_URL})\n")
    if not links:
        links = config.TIM_TIM_URL

    channel_links = links.split(',')
    # generator
    channels = ((get_channel_name(channel_link), channel_link)
                for channel_link in channel_links)

    # create a webdriver instance
    driver = webdriver.Chrome("/Users/mmishche/dev/home/youtube/chromedriver")
    try:
        for channel_name, channel_link in channels:
            # navigate to the webpage with the desired element
            driver.get(f"{channel_link}/video")

            # Click the "Accept all" button to skip cookie banner (only once)
            agree_button = driver.find_element_by_xpath(
                "//button[@aria-label='Accept all']")
            if agree_button:
                agree_button.click()

            # Scroll to the end of the page once, also download next 30 videos
            app = driver.find_element_by_tag_name("ytd-app")
            driver.execute_script(
                f"window.scrollTo(0, {app.size['height']});")

            # sleep 3 seconds to wait page load
            time.sleep(3)

            # parse the element of interest (item: preview + title + details)
            screenshots_elements = driver.find_elements_by_tag_name(
                "ytd-rich-item-renderer")
            logging.info("Found %s screenshot elements",
                         len(screenshots_elements))

            # Create a pool of worker processes
            with Pool(processes=5) as pool:
                # Use the map method to call the fetch_and_filter_element
                # function for each element in parallel
                filtered_screenshot_elements = pool.map(
                    fetch_and_filter_element, screenshots_elements)
                # remove None items
                filtered_screenshot_elements = [
                    el for el in filtered_screenshot_elements if el]

            logging.info("Found %s filtered screenshot elements",
                         len(filtered_screenshot_elements))

            response = send_message_telegram_bot(channel_name)
            if response.status_code != 200:
                raise TelegramSendMessageFailedError(
                    f'Error sending photo: {response.status_code} '
                    f'{response.text}')
            # take a screenshot of the element and save it to a file
            for title, video_link, el in filtered_screenshot_elements:
                screenshot_path = f'{config.SCREENSHOTS_PATH}/{title}.png'
                # Creating an instance of ActionChains class for each element
                action = ActionChains(driver)
                # Hovering over the element
                action.move_to_element(el).perform()
                el.screenshot(screenshot_path)
                # send screenshot to the
                response = send_picture_telegram_bot(screenshot_path,
                                                     video_link)
                if response.status_code != 200:
                    raise TelegramSendPictureFailedError(
                        f'Error sending photo: {response.status_code} '
                        f'{response.text}')

    except Exception as err:
        logging.error(err)
    finally:
        # close the browser
        driver.quit()


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN var is not set")

    main()
