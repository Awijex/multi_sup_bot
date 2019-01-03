from flask import Flask, request
from flask_sslify import SSLify
from core.structure import check_structure
from core.models import create_database
check_structure()
from core import data
from core.state import states
import telebot

APP = Flask(__name__)
DB, User = create_database(APP)


def check_state(message):
    pass


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
    if not User.query.filter_by(user_id=message.chat.id).first():
        user = User(message.chat.id, message.text)
        DB.session.add(user)
        DB.session.commit()
        BOT.send_message(message.chat.id, 'Hello, ' + message.chat.first_name)
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    weather_button = telebot.types.KeyboardButton(text='Погода')
    keyboard.add(weather_button)
    BOT.send_message(message.chat.id, 'Вот что я могу:', reply_markup=keyboard)


@BOT.message_handler(content_types=['text'])
def text(message):
    print(message.text)


def main():
    SSLify(APP)
    APP.run()


if __name__ == '__main__':
    main()
