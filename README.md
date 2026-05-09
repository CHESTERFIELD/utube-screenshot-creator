# Getting start
### Prerequisites
1. Python 3.9+
2. Create telegram bot and get bot token, more by following https://core.telegram.org/bots/tutorial
3. Get your telegram chat id, to do that you can use a bot like `@RawDataBot`: search for it in Telegram, start a chat, and it will message you your ID (a long number under "chat" -> "id") for private chats
### Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
### Install dependencies 
```bash
# install python and application dependencies
python3 -m pip install -r req.txt && make update-driver && mkdir screenshots
```
### Adjust .env file
```
# copy and input your own creds to the .env file in the root folder
BOT_TOKEN="YOUR_BOT_TOKEN"
SCREENSHOTS_PATH="./screenshots"
CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
CHROMEDRIVER_PATH="./chromedriver.exe"

# to use youtube API client instead of legacy pytube set next:
USE_YOUTUBE_API="True"
USE_BATCH_API="True"
YOUTUBE_API_KEY="GCP_API_KEY_WITH_ENABLED_YOUTUBE_API_V3"

# enale workaround for issue with banner
CUSTOM_WORKAROUND_ENABLED="False"

# if True skip second page with videos
SKIP_SECOND_PAGE="False"

# if True skip filtering by date
SKIP_FILTERING_BY_DATE="False"

# if True use youtube locale settings, otherwise use current OS language settings
# see "Chrome and Youtube Localization" section below for additional settings
USE_YOUTUBE_LOCALE="False"
```
### Run
```bash
make run
```
### Update chromedriver
```bash
make update-driver
```
NOTE: do not run if no issue occured saying that browser and chromedriver versions do not match.

### Chrome and Youtube Localization 
To be able to run application in different language set config variables in `.env` file as specified below:
```
# For spanish use
OS_PRIMARY_LANGUAGE="ES"
CHROME_LANG="es-ES"
YOUTUBE_HL="es"
YOUTUBE_GL="ES"
YOUTUBE_ACCEPT_LANGUAGES="es-ES,es,en-US,en"

# For english (US) use
OS_PRIMARY_LANGUAGE="EN"
CHROME_LANG="en-US"
YOUTUBE_HL="en"
YOUTUBE_GL="EN"
YOUTUBE_ACCEPT_LANGUAGES="en-US,en"
```
By default will use current OS language settings and current region that youtube determinate dynamically if nothing specified.
# Known issues
## Pytube
1. Issue related to channel video link new format with "@" character - https://github.com/atrichkov/pytube/commit/390fc1d7c4e88685fc64fcf44b07d1b9c0b0b5b6
2. Empty channel videos - https://github.com/pytube/pytube/pull/1409/files
3. InnerTube client type "ANDROID" version doesn't work - https://github.com/pytube/pytube/issues/1565
