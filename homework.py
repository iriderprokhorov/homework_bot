# from black import err
# from http import HTTPStatus

# from asyncio.log import logger
import logging
import requests
import os
import telegram
import time

from dotenv import load_dotenv


load_dotenv()


# Здесь задана глобальная конфигурация для логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)

PRACTICUM_TOKEN = os.getenv('P_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def send_message(bot, message):
    """function send message"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f'Can t send message to telegram: {error}'
        logging.error(message)
    else:
        logging.info('successful send message to telegram')


def get_api_answer(current_timestamp):
    """function getting response from api"""
    timestamp = current_timestamp or int(time.time())
    # 1642412129
    params = {'from_date': timestamp}

    try:
        homework_response = requests.get(
            url=ENDPOINT, headers=HEADERS, params=params
        )
    except requests.exceptions.RequestException as error:
        message = f"http response is not 200: {error}"
        logging.error(message)
    else:
        if homework_response.status_code != 200:
            logging.error("Http response is not 200")
        else:
            return homework_response.json()


def check_response(response):
    """function validation response"""
    try:
        checked_response = response['homeworks']
    except KeyError as error:
        message = f'response is not consist necessery keys {error}'
        logging.error(message)
    else:
        if not isinstance(checked_response, list):
            logging.error("homeworks is wrong type")
        if not bool(checked_response):
            logging.error("homeworks is empty")
        else:
            return checked_response


def parse_status(homework):
    """Check homework status"""
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    except KeyError as error:
        # raise KeyError('ststus is not doc')
        message = f'response is not consist necessery keys {error}'
        logging.error(message)
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check token available"""
    try:
        for token in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
            if not token:
                raise Exception('Token is not available')
    except Exception as error:
        message = f'Token is not available: {error}'
        logging.critical(message)
        # send_message(bot, message)
    else:
        return True


def main():
    """Main module"""
    try:
        check_tokens() is True
    except Exception as error:
        message = f'Token is not available: {error}'
        logging.critical(message)
    else:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())

    cache = ()

    while True:
        try:
            response = get_api_answer(current_timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            if len(cache) == 0:
                cache = parse_status(response)
            else:
                if cache == parse_status(response):
                    send_message(bot, parse_status(response))
                    print(parse_status(response))
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
