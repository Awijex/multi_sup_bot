import os


TOKEN = open(os.path.join(os.path.abspath('core'), 'token')).read()
URL = open(os.path.join(os.path.abspath('core'), 'url')).read()
WEATHER_API_KEY = open(os.path.join(os.path.abspath('core'), 'weather_api_key')).read()
