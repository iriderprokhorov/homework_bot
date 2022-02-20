import logging
import json
import os
import requests
import sys
import telegram
import time

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv("P_TOKEN")
TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Function for send message."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f"Can t send message to telegram: {error}"
        logger.error(message)
    else:
        logger.info("successful send message to telegram")


def get_api_answer(current_timestamp):
    """Function getting response from api."""
    timestamp = current_timestamp or int(time.time())
    # 1642412129
    params = {"from_date": timestamp}

    try:
        homework_response = requests.get(
            url=ENDPOINT, headers=HEADERS, params=params
        )
    except requests.ConnectionError as error:
        message = f"connection error: {error}"
        logger.error(message)
    if homework_response.status_code != HTTPStatus.OK.value:
        logger.error(homework_response.status_code)
        raise requests.HTTPError("Http response is not 200")
    else:
        try:
            serialized_response = homework_response.json()
        except json.decoder.JSONDecodeError as error:
            message = f"can t serialize to json: {error}"
            logger.error(message)
        return serialized_response


def check_response(response):
    """Function validation response."""
    try:
        homeworks = response["homeworks"]
    except KeyError as error:
        message = f"response is not consist necessery keys {error}"
        logger.error(message)
        raise KeyError(message)
    else:
        if not isinstance(homeworks, list):
            logger.error("homeworks is wrong type")
            raise TypeError("homeworks is wrong type")
        if not homeworks:
            logger.error(homeworks)
            raise KeyError("homeworks is empty")
        return homeworks


def parse_status(homework):
    """Check homework status."""
    try:
        homework_name = homework["homework_name"]
        homework_status = homework["status"]
    except KeyError as error:
        message = f"response is not consist necessery keys {error}"
        logger.error(message)
        raise KeyError("response is not consist necessery keys")
    else:
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
            return (
                f"Изменился статус проверки работы"
                f' "{homework_name}". {verdict}'
            )
        else:
            logger.error(homework_status)
            raise Exception("homework status is not defined")


def check_tokens():
    """Check token availability."""
    dict_token = {
        "practicum_token": PRACTICUM_TOKEN,
        "telegram_token": TELEGRAM_TOKEN,
        "telecgram_chat_id": TELEGRAM_CHAT_ID,
    }
    for token, value in dict_token.items():
        if not value:
            logger.critical(f"{token} is not available")
            return False
    return True


def main():
    """Main module."""
    if check_tokens() is True:
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
        except Exception as error:
            message = f"BOT is not initialized: {error}"
            logger.error(message)
        current_timestamp = int(time.time()) - 36000
    else:
        return

    last_result = ""

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            verdict = parse_status(homeworks[0])
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
        else:
            logger.info(verdict)
            if last_result == verdict:
                logger.info("not change")
            else:
                last_result = verdict
                send_message(bot, verdict)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
