import os
import telegram
import config


BOT = telegram.Bot(token=config.BOT_TOKEN)
CHAT_ID_KWARGS = {'chat_id': config.CHAT_ID}


def send_message_telegram_bot(message: str):
    # Send message
    data = {'text': message}
    return BOT.send_message(**CHAT_ID_KWARGS, **data)


def send_picture_telegram_bot(picture_path: str, caption: str):
    # Send photo and caption to it
    data = {'photo': open(picture_path, 'rb'), 'caption': caption}
    return BOT.send_photo(**CHAT_ID_KWARGS, **data)


def main():
    # Replace the file path with the path to your image file
    image_path = os.path.join(config.SCREENSHOTS_PATH, "test.png")

    response = send_message_telegram_bot("test")
    # Check the response
    if response.status_code == 200:
        print('Photo sent successfully!')
    else:
        print(f'Error sending photo: {response.status_code} {response.text}')

    response = send_picture_telegram_bot(image_path, "test caption")
    # Check the response
    if response.status_code == 200:
        print('Photo sent successfully!')
    else:
        print(f'Error sending photo: {response.status_code} {response.text}')


if __name__ == "__main__":
    main()
