"""Utils to find elements in driver."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from typing import Optional


def find_screenshot_elements(driver: webdriver.Chrome) -> list[
        WebElement]:
    """Find elements to scheenshot on the page."""
    return driver.find_elements(
        By.CSS_SELECTOR, "yt-lockup-view-model.ytLockupViewModelWrapper")
    
    
def find_thumbnail_img(element) -> Optional[webdriver.remote.webelement.WebElement]:
    try:
        imgs = element.find_elements(By.CSS_SELECTOR, "ytd-thumbnail img")
        if imgs:
            return imgs[0]
        imgs = element.find_elements(By.CSS_SELECTOR, "img#img")
        if imgs:
            return imgs[0]
    except Exception:
        return None
    return None


def find_cookie_button(driver: webdriver.Chrome, text: str) -> WebElement:
    """Find cookie button by aria-label."""
    return driver.find_element(By.XPATH,
        f"//button[@aria-label='{text}']")
    

def find_div_text_element(driver: webdriver.Chrome, text: str) -> WebElement:
    """Find div element by text."""
    return driver.find_element(By.XPATH, f"//div[text()='{text}']")


def find_element_by_tag_name(driver: webdriver.Chrome, text: str) -> WebElement:
    """Find element by tag name."""
    return driver.find_element(By.TAG_NAME, text)
