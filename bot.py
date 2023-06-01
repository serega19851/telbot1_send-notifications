import requests
import telegram
from time import sleep
import sys
from environs import Env


def sends_notifications(sms, telegram_token, telegram_chat_id):
    bot = telegram.Bot(token=telegram_token)
    bot.send_message(chat_id=telegram_chat_id, text=sms)


def checks_status_server(response, params, dvmn_url, headers):
    if response.json()['status'] == 'found':
        response = requests.get(
                    dvmn_url,
                    headers=headers,
                    params=params,
                    timeout=90
                    )
        response.raise_for_status()

        report = (
            'У вас проверили работу '
            f'"{response.json()["new_attempts"][0]["lesson_title"]}" '
            f'{response.json()["new_attempts"][0]["lesson_url"]}'
            '\n\nК сожалению, в работе нашлись ошибки'
            if response.json()["new_attempts"][0]["is_negative"]
            else 'У вас проверили работу'
            f'"{response.json()["new_attempts"][0]["lesson_title"]}"'
            '\n\nПреподавателю все понравилось,можно приступать '
            'к следующему уроку!'
            )
        return report
    return None 

def main():
    env = Env()
    env.read_env()
    devman_token = env.str('TOKEN_DVMN')
    telegram_token = env.str('TELEGRAM_TOKEN')
    telegram_chat_id = env.str('TELEGRAM_CHAT_ID')
    headers = {'Authorization': f'Token {devman_token}'}
    dvmn_url = 'https://dvmn.org/api/long_polling/'
    params =None

    while True:
        try:
            response = requests.get(
                    dvmn_url,
                    headers=headers,
                    params=params,
                    timeout=90
                    )
            response.raise_for_status
            report = checks_status_server(response, params, dvmn_url, headers)
            if report:
                sends_notifications(report, telegram_token, telegram_chat_id)
        except requests.exceptions.ReadTimeout as read_timeout:
            sys.stderr.write(f'Превышено время ожидания\n{read_timeout}\n\n')
            sleep(5)
        except requests.exceptions.ConnectionError as connect_error:
            sys.stderr.write(f'Произошёл сетевой сбой\n{connect_error}\n\n')
            sleep(5)


if __name__ == '__main__':
    main()
