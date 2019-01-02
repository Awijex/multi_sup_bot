from flask import Flask, request
from flask_sslify import SSLify
from core.structure import check_structure
check_structure()
from core import data
import telebot

APP = Flask(__name__)


def create_bot():
    bot = telebot.TeleBot(token=data.TOKEN)
    bot.remove_webhook()
    bot.set_webhook(url=data.URL + '/' + data.TOKEN)
    return bot


BOT = create_bot()


@APP.route('/' + data.TOKEN, methods=['POST'])
def create_webhook():
    BOT.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
    return 'ok', 200


@BOT.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    weather_button = telebot.types.KeyboardButton(text='Погода')
    keyboard.add(weather_button)
    BOT.send_message(message.chat.id, text='Выбери что-нибудь', reply_markup=keyboard)


@BOT.message_handler(content_types=['text'])
def text(message):
    BOT.send_message(message.chat.id, message.text)
    print(message.text)


def main():
    SSLify(APP)
    APP.run()


if __name__ == '__main__':
    main()
