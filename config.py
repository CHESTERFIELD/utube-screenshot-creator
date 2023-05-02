import datetime
import os
from dotenv import load_dotenv

# Load config from .env file
load_dotenv()

# App
SCREENSHOTS_PATH = os.getenv("SCREENSHOTS_PATH")
TRUE_VALEUS = (1, 'y', 'yes', 't', 'T', 'true')
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in TRUE_VALEUS
# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# Youtube
YOUTUBE_URL = "https://www.youtube.com"
TIM_TIM_URL = f"{YOUTUBE_URL}/@TIMTIN"
# Selenium
OS_PRIMARY_LANGUAGE = os.getenv("OS_PRIMARY_LANGUAGE", "EN")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

# Constants
CLAUSE_100K = 10 ** 5
CLAUSE_200K = CLAUSE_100K * 2
CLAUSE_300K = CLAUSE_100K * 3
NOW = datetime.datetime.now()
FIFTEEN_DAYS_AGO = NOW - datetime.timedelta(days=15)
FORTY_FIVE_DAYS_AGO = NOW - datetime.timedelta(days=45)
