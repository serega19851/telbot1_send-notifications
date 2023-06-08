import requests
import telegram
from time import sleep
import sys
from environs import Env
import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__file__)


class TelegramLogsHandler(logging.Handler):
    def __init__(self, chat_id, bot):
        super().__init__()
        self.chat_id = chat_id
        self.bot = bot

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env()
    devman_token = env.str('TOKEN_DVMN')
    telegram_token = env.str('TELEGRAM_TOKEN')
    telegram_chat_id = env.str('TELEGRAM_CHAT_ID')
    headers = {'Authorization': f'Token {devman_token}'}
    dvmn_url = 'https://dvmn.org/api/long_polling/'
    params = {'timestamp': None}

    bot = telegram.Bot(token=telegram_token)
    logging.basicConfig(
            filename='app.log',
            format='%(name)s - %(levelname)s - %(asctime)s - %(message)s',
            filemode='w',
            level=logging.INFO
            )
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(telegram_chat_id, bot))
    handler = RotatingFileHandler('app.log', maxBytes=1000, backupCount=2)
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.addHandler(handler)
    logger.info("Бот запущен")

    while True:
        try:
            response = requests.get(
                    dvmn_url,
                    headers=headers,
                    params=params,
                    )
            response.raise_for_status()
            work_checks = response.json()

            if work_checks['status'] == 'found':
                new_attempt = work_checks["new_attempts"][0]
                report = (
                    'У вас проверили работу '
                    f'"{new_attempt["lesson_title"]}" '
                    f'{new_attempt["lesson_url"]}'
                    '\n\nК сожалению, в работе нашлись ошибки'
                    if new_attempt["is_negative"]
                    else 'У вас проверили работу'
                    f'"{new_attempt["lesson_title"]}"'
                    '\n\nПреподавателю все понравилось,можно приступать '
                    'к следующему уроку!'
                    )
                bot.send_message(chat_id=telegram_chat_id, text=report)
                params = {
                        'timestamp': work_checks.get(
                            'last_attempt_timestamp'
                            )
                        }
            else:
                params = {
                        'timestamp': work_checks.get(
                            'timestamp_to_request'
                            )
                        }
        except requests.exceptions.ReadTimeout as read_timeout:
            logger.warning(f'Превышено время ожидания\n{read_timeout}\n\n')
        except requests.exceptions.ConnectionError as connect_error:
            logger.warning(f'Произошёл сетевой сбой\n{connect_error}\n\n')
            sleep(20)


if __name__ == '__main__':
    main()
