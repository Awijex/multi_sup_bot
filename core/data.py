import os


TOKEN = open(os.path.join(os.path.abspath('core'), 'token')).read().strip()
URL = open(os.path.join(os.path.abspath('core'), 'url')).read().strip()
WEATHER_API_KEY = open(os.path.join(os.path.abspath('core'), 'weather_api_key')).read().strip()
NEWS_API_KEY = open(os.path.join(os.path.abspath('core'), 'news_api_key')).read().strip()
