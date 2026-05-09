from cgitb import text
from selenium import webdriver

from youtube_find_elements_utils import (
    find_cookie_button, find_div_text_element
)

import config
import logging


# Map OS language to cookie button label
if config.OS_PRIMARY_LANGUAGE == config.UA_LANGUAGE:
    COOKIE_BUTTON_LABEL = "Прийняти всі"
elif config.OS_PRIMARY_LANGUAGE == config.ES_LANGUAGE:
    COOKIE_BUTTON_LABEL = "Aceptar todo"
else:
    COOKIE_BUTTON_LABEL = "Accept all"
    
# Map OS language to navigation text
if config.OS_PRIMARY_LANGUAGE == config.UA_LANGUAGE:
    NAV_HOME_TEXT = "Головна"
    NAV_VIDEOS_TEXT = "Відео"
elif config.OS_PRIMARY_LANGUAGE == config.ES_LANGUAGE:
    NAV_HOME_TEXT = "Inicio"
    NAV_VIDEOS_TEXT = "Videos"
else:
    NAV_HOME_TEXT = "Home"
    NAV_VIDEOS_TEXT = "Videos"


def handle_cookie_banner(driver: webdriver.Chrome):
    """Handle cookie banner by clicking the accept button.
    
    Args:
        driver: Selenium WebDriver instance
    
    Raises:
        Exception: If the cookie button is not found
    """
    try:
        agree_button = find_cookie_button(driver, COOKIE_BUTTON_LABEL)
        agree_button.click()
    except Exception:
        logging.exception("Unable to find cookie button.")
        raise
        

def navigate_to_videos_page(driver: webdriver.Chrome):
    """Custom workaround to navigate quickly between home and videos 
    pages to address the issue where channel home picture covers 
    first row of videos pictures on videos page.
    
    This function clicks on the home button and then on the videos button
    to navigate to the videos page immediately without waiting for the 
    page to load.
    
    Args:
        driver: Selenium WebDriver instance.
        
    Raises:
        Exception: If the navigation buttons are not found or clicking 
        fails.
    """
    try:
        home_button = find_div_text_element(driver, NAV_HOME_TEXT)
        home_button.click()
        
        videos_button = find_div_text_element(driver, NAV_VIDEOS_TEXT)
        videos_button.click()

    except Exception:
        logging.exception("Unable to navigate between home and videos pages.")
        raise
        