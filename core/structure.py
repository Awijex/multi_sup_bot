import os


def check_structure():
    files = ('token', 'url', 'weather_api_key', 'news_api_key')
    for file in files:
        if not os.path.exists(file):
            open(file, 'w')


if __name__ == '__main__':
    check_structure()
