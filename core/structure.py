import os


def check_structure():
    files = ('token', 'url')
    for file in files:
        if not os.path.exists(os.path.join(os.path.abspath('core'), file)):
            open(file, 'w')
