"""Application config module."""
import datetime
import os
from dotenv import load_dotenv

# Load config from .env file
load_dotenv()

# App
SCREENSHOTS_PATH = os.getenv("SCREENSHOTS_PATH")
TRUE_VALEUS = (1, 'y', 'yes', 't', 'T', 'true')
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in TRUE_VALEUS
# Enable execution of custom workaround
CUSTOM_WORKAROUND_ENABLED = os.getenv(
    "CUSTOM_WORKAROUND_ENABLED", "false").lower() in TRUE_VALEUS

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Youtube
YOUTUBE_URL = "https://www.youtube.com"
TIM_TIM_URL = f"{YOUTUBE_URL}/@TIMTIN"
YOUTUBE_HL = os.getenv("YOUTUBE_HL", "es")
YOUTUBE_GL = os.getenv("YOUTUBE_GL", "ES")
YOUTUBE_ACCEPT_LANGUAGES = os.getenv(
    "YOUTUBE_ACCEPT_LANGUAGES",
    "es-ES,es,en-US,en",
)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
USE_YOUTUBE_API = os.getenv("USE_YOUTUBE_API", "false").lower() in TRUE_VALEUS
USE_YOUTUBE_LOCALE = os.getenv("USE_YOUTUBE_LOCALE", "false").lower() in TRUE_VALEUS
USE_BATCH_API = os.getenv("USE_BATCH_API", "false").lower() in TRUE_VALEUS
USE_FORHANDLE_API = os.getenv("USE_FORHANDLE_API", "true").lower() in TRUE_VALEUS

# Selenium
EN_LANGUAGE = "EN"
UA_LANGUAGE = "UA"
ES_LANGUAGE = "ES"
OS_PRIMARY_LANGUAGE = os.getenv("OS_PRIMARY_LANGUAGE", EN_LANGUAGE)

# Chromedriver
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")
if not os.path.exists(CHROMEDRIVER_PATH):
    CHROMEDRIVER_PATH = f"{CHROMEDRIVER_PATH}.exe"
    if not os.path.exists(CHROMEDRIVER_PATH):
        raise FileNotFoundError("Chromedriver not found")

# Chrome
CHROME_LANG = os.getenv("CHROME_LANG", "en-US")

# Constants
CLAUSE_100K = 10 ** 5
CLAUSE_200K = CLAUSE_100K * 2
CLAUSE_300K = CLAUSE_100K * 3
NOW = datetime.datetime.now()
FIFTEEN_DAYS_AGO = NOW - datetime.timedelta(days=15)
FORTY_FIVE_DAYS_AGO = NOW - datetime.timedelta(days=45)

# if was request to be able to make this configurable
SKIP_SECOND_PAGE = os.getenv("SKIP_SECOND_PAGE", "false").lower() in TRUE_VALEUS

SKIP_FILTERING_BY_DATE = os.getenv("SKIP_FILTERING_BY_DATE", "false").lower() in TRUE_VALEUS

TEST_NETWORK_CONDITIONS = os.getenv("TEST_NETWORK_CONDITIONS", "false").lower() in TRUE_VALEUS
