# from black import err

import logging
import requests
import os
import telegram
import time

from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger("homework_check_bot")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)


class MsgError(Exception):
    pass


PRACTICUM_TOKEN = os.getenv("P_TOKEN")
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RETRY_TIME = 6
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info("send_message")


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": 1642412129}
    # Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами
    homework_response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return homework_response.json()


def check_response(response):
    try:
        checked_response = response.get("homeworks")
        return checked_response
    except Exception as error:
        message = f"Сбой в работе программы: {error}"


def parse_status(homework):
    """Check homework status"""
    homework_name = homework.get("homeworks")
    homework_status = homework.get("homeworks")
    homework_name = homework_name[0].get("homework_name")
    verdict = homework_status[0].get("status")

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check token available"""
    try:
        for token in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
            if not token:
                raise MsgError("Token is not available")
    except MsgError as error:
        message = f"Token is not available: {error}"
        logger.info(message)
        # send_message(bot, message)
    except Exception as error:
        message = f"Token is not available: {error}"
        logger.info(message)
        # send_message(bot, message)


def main():
    """Main module"""

    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    cache = ()

    while True:
        try:
            response = get_api_answer(current_timestamp)

            if len(cache) == 0:
                cache = parse_status(response)
            else:
                if cache != parse_status(response):
                    # send_message(bot, parse_status(response))
                    send_message(bot, parse_status(response))

            # current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            ...
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == "__main__":
    main()
