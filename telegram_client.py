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
