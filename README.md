# Getting start
### Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
```
### Install dependencies 
```bash
python3 -m pip install req.txt
# download chromedriver and put executable one to the root folder
wget https://chromedriver.storage.googleapis.com/112.0.5615.28/chromedriver_mac_arm64.zip
```
### Adjust .env file
```
# copy and input your own creds to the .env file in the root folder
BOT_TOKEN="YOUR_BOT_TOKEN"
SCREENSHOTS_PATH="YOUR_SCREENSHOT_PATH"
CHAT_ID="YOUT_TELEGRAM_CHAT_ID"
OS_PRIMARY_LANGUAGE="YOUR_OS_PRIMARY_LANGUAGE_EN_OR_UA"
CHROMEDRIVER_PATH="YOUR_CHROMEDRIVER_PATH"
```
### Run
```bash
make run
```

# Known issues
## Pytube
1. Issue related to channel video link new format with "@" character - https://github.com/atrichkov/pytube/commit/390fc1d7c4e88685fc64fcf44b07d1b9c0b0b5b6
2. Empty channel videos - https://github.com/pytube/pytube/pull/1409/files
3. InnerTube client type "ANDROID" version doesn't work - https://github.com/pytube/pytube/issues/1565