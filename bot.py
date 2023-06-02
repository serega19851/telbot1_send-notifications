import requests
import telegram
from time import sleep
import sys
from environs import Env


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

    while True:
        try:
            response = requests.get(
                    dvmn_url,
                    headers=headers,
                    params=params,
                    timeout=90
                    )
            response.raise_for_status()
            info_about_works_check = response.json()

            if info_about_works_check['status'] == 'found':
                new_attempt = info_about_works_check["new_attempts"][0]
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
                        'timestamp': info_about_works_check.get(
                            'last_attempt_timestamp'
                            )
                        }
            else:
                params = {
                        'timestamp': info_about_works_check.get(
                            'timestamp_to_request'
                            )
                        }
        except requests.exceptions.ReadTimeout as read_timeout:
            sys.stderr.write(f'Превышено время ожидания\n{read_timeout}\n\n')
        except requests.exceptions.ConnectionError as connect_error:
            sys.stderr.write(f'Произошёл сетевой сбой\n{connect_error}\n\n')
            sleep(5)


if __name__ == '__main__':
    main()
