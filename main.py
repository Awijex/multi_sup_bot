import json
import telebot
import requests
import xmltodict
import time
from collections import namedtuple
from flask import Flask, request
from flask_sslify import SSLify
from core.models import create_database
from core import data
from core.state import states

APP = Flask(__name__)
SSLify(APP)

DB, USER = create_database(APP)
KEYBOARDS = {}


def check_state(message):
    user = USER.query.filter_by(user_id=message.chat.id).first()
    if message.text in states[user.state]:
        user.state = states[user.state][message.text] if states[user.state][message.text] in states else user.state
        DB.session.commit()
        return user.state
    return False


def create_buttons():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = (telebot.types.KeyboardButton(text='{}'.format(i)) for i in ('Погода', 'Курс валют', 'Новости'))
    keyboard.add(*buttons)

    KEYBOARDS['/start'] = {'keyboard': keyboard, 'text': 'Вот что я могу:'}

    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    coordinates_button = telebot.types.KeyboardButton(text='По координатам', request_location=True)
    back_button = telebot.types.KeyboardButton(text='Назад')
    keyboard.add(coordinates_button, back_button)

    KEYBOARDS['Погода'] = {'keyboard': keyboard, 'text': 'Погода:'}

    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = (telebot.types.KeyboardButton(text='{}'.format(i)) for i in ('Россия', 'Беларусь', 'Назад'))
    keyboard.add(*buttons)

    KEYBOARDS['Курс валют'] = {'keyboard': keyboard, 'text': 'Выбери страну:'}

    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = (telebot.types.KeyboardButton(text='{}'.format(i)) for i in ('Топ 10', 'Назад'))
    keyboard.add(*buttons)

    KEYBOARDS['Новости'] = {'keyboard': keyboard, 'text': 'Что ты хочешь посмотреть?'}


def create_bot():
    bot = telebot.TeleBot(token=data.TOKEN, threaded=False)
    bot.remove_webhook()
    bot.set_webhook(url='/'.join((data.URL, data.TOKEN)))
    return bot


def short_url(url):
    response = json.loads(requests.post('https://to.click/api/v1/links',
                                        json={'data': {'type': 'link', 'attributes': {'web_url': url}}},
                                        headers={'X-AUTH-TOKEN': 'L1VwmEW3pniG3LSFDV3Z4yPc',
                                                 'Content-Type': 'application/json'}).text)
    return response['data']['attributes']['full_url']


BOT = create_bot()


@APP.route('/')
def get_route():
    return 'ok'


@APP.route('/' + data.TOKEN, methods=["POST"])
def update_messages():
    BOT.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200


@BOT.message_handler(commands=['start'])
def start(message):
    if not USER.query.filter_by(user_id=message.chat.id).first():
        user = USER(message.chat.id, message.text)
        DB.session.add(user)
        DB.session.commit()
        BOT.send_message(message.chat.id, 'Привет, ' + message.chat.first_name)
    else:
        user = USER.query.filter_by(user_id=message.chat.id).first()
        user.state = message.text
        DB.session.commit()

    BOT.send_message(message.chat.id, KEYBOARDS[message.text]['text'],
                     reply_markup=KEYBOARDS[message.text]['keyboard'])


class News:

    @staticmethod
    @BOT.message_handler(regexp='Новости')
    def news(message):
        if check_state(message):
            BOT.send_message(message.chat.id, KEYBOARDS[message.text]['text'],
                             reply_markup=KEYBOARDS[message.text]['keyboard'])
        else:
            BOT.send_message(message.chat.id, 'Неверная команда')

    @staticmethod
    @BOT.message_handler(regexp='Топ 10')
    def top_news(message):
        if check_state(message):
            for url, title in News.get_top_news():
                BOT.send_message(message.chat.id, f'<b>{title}</b>\nhttps://t.me/iv?url={url}&rhash=49c3eabf2e6215',
                                 parse_mode='html')
                time.sleep(0.5)

    @staticmethod
    def get_top_news():
        news = json.loads(requests.get(f'https://newsapi.org/v2/top-headlines?sources=lenta&'
                          f'apiKey={data.NEWS_API_KEY}').text)
        tpl = namedtuple('News', ['url', 'title'])
        return [tpl(url=i['url'], title=i['title']) for i in news['articles']]


class Weather:

    @staticmethod
    def get_weather_by_location(location):
        response = json.loads(requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?lat={location.latitude}&lon={location.longitude}'
            f'&APPID={data.WEATHER_API_KEY}&units=metric'
        ).text)
        weather = {'temp': response['main']['temp'],
                   'wind': response['wind']['speed'],
                   'clouds': response['clouds']['all'],
                   }
        return weather

    @staticmethod
    def get_weather_by_city(city):
        """
        :param city
        :return: city weather
        """
        try:
            response = json.loads(requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}'
                                               f'&APPID={data.WEATHER_API_KEY}&units=metric'
                                               ).text)
            weather = {'temp': response['main']['temp'],
                       'wind': response['wind']['speed'],
                       'clouds': response['clouds']['all'],
                       }
            return weather
        except KeyError:
            return

    @staticmethod
    @BOT.message_handler(regexp='Погода')
    def weather(message):
        if check_state(message):
            BOT.send_message(message.chat.id, KEYBOARDS[message.text]['text'],
                             reply_markup=KEYBOARDS[message.text]['keyboard'])
        else:
            BOT.send_message(message.chat.id, 'Неверная команда')

    @staticmethod
    @BOT.message_handler(content_types=['location'])
    def coordinates(message):
        user = USER.query.filter_by(user_id=message.chat.id).first()
        if user.state == 'Погода':
            weather = Weather.get_weather_by_location(message.location)
            BOT.send_message(message.chat.id, f'Темпаратура: {weather["temp"]}\n'
                                              f'Ветер: {weather["wind"]}\n'
                                              f'Облачность: {weather["clouds"]}\n')


class Rate:

    @staticmethod
    def get_belarusian_rate():
        currencies = ('USD', 'EUR', 'RUB')
        response = requests.get('http://www.nbrb.by/API/ExRates/Rates?Periodicity=0').text
        response = json.loads(response)
        response = {i['Cur_Abbreviation']: i for i in response}
        answer = []
        for i in currencies:
            answer.append(' '.join((str(response[i]['Cur_Scale']), i,
                                    'стоит' if response[i]['Cur_Scale'] == 1 else 'стоят',
                                    str(response[i]['Cur_OfficialRate']), 'BYN')))
        return '\n'.join(answer)

    @staticmethod
    def get_russian_rate():
        currencies = ('USD', 'EUR')
        response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp').text
        response = xmltodict.parse(response)
        response = {i['CharCode']: i for i in response['ValCurs']['Valute']}
        answer = []
        for i in currencies:
            answer.append(' '.join((str(response[i]['Nominal']), i,
                                    'стоит' if int(response[i]['Nominal']) == 1 else 'стоят',
                                    str(response[i]['Value']), 'RUB')))
        return '\n'.join(answer).replace(',', '.')

    @staticmethod
    @BOT.message_handler(regexp='Курс валют')
    def moneys(message):
        if check_state(message):
            BOT.send_message(message.chat.id, KEYBOARDS[message.text]['text'],
                             reply_markup=KEYBOARDS[message.text]['keyboard'])
        else:
            BOT.send_message(message.chat.id, 'Неверная команда')


@BOT.message_handler(regexp='Беларусь|Россия')
def route_country(message):
    state = check_state(message)
    if state == 'Курс валют':
        if message.text == 'Беларусь':
            BOT.send_message(message.chat.id, Rate.get_belarusian_rate())
        elif message.text == 'Россия':
            BOT.send_message(message.chat.id, Rate.get_russian_rate())
    else:
        BOT.send_message(message.chat.id, 'Неверная команда')


@BOT.message_handler(regexp='Назад')
def back(message):
    if check_state(message):
        user = USER.query.filter_by(user_id=message.chat.id).first()
        BOT.send_message(message.chat.id, KEYBOARDS[user.state]['text'],
                         reply_markup=KEYBOARDS[user.state]['keyboard'])
    else:
        BOT.send_message(message.chat.id, 'Неверная команда')


@BOT.message_handler(content_types=['text'])
def text(message):
    BOT.send_message(message.chat.id, 'Неверная команда')


def main():
    create_buttons()


main()


if __name__ == '__main__':
    APP.run()
