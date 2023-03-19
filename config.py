import datetime
import os

# App config
SCREENSHOTS_PATH = os.getenv("SCREENSHOTS_PATH",
                             "/Users/mmishche/dev/home/youtube/screenshots")

# Telegram client config
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Youtube common
YOUTUBE_URL = "https://www.youtube.com"
TIM_TIM_URL = f"{YOUTUBE_URL}/@TIMTIN"

# Selenium client config
# empty so far

# Constants
CLAUSE_100K = 10 ** 5
CLAUSE_300K = CLAUSE_100K * 3
NOW = datetime.datetime.now()
FIFTEEN_DAYS_AGO = NOW - datetime.timedelta(days=15)
FORTY_FIVE_DAYS_AGO = NOW - datetime.timedelta(days=45)