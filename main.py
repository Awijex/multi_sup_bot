import telebot
from flask import Flask, request
from flask_sslify import SSLify
from core import data


APP = Flask(__name__)


def create_bot():
    bot = telebot.TeleBot(token=data.TOKEN)
    bot.remove_webhook()
    bot.set_webhook(url=data.URL + '/' + data.TOKEN)
    return bot


BOT = create_bot()


@APP.route('/' + data.TOKEN)
def create_webhook():
    BOT.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
    return 'ok', 200


def main():
    SSLify(APP)
    APP.run()


if __name__ == '__main__':
    main()
