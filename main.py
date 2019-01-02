import telebot
import flask


def main():
    bot = telebot.TeleBot(token=open('token'))


if __name__ == '__main__':
    main()
