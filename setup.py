from setuptools import find_packages, setup

setup(
    name='multi_sup_bot',
    version='0.0',
    packages=find_packages(),
    py_modules=['main'],
    entry_points={
        'console_scripts': ['multi_sup_bot = main:main']
    }
)
