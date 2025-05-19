from setuptools import setup

APP = ['read-file.py']
DATA_FILES = []
OPTIONS = {
    # 'argv_emulation': True,  ← REMOVE or comment this line
    'packages': ['openpyxl', 'requests', 'duckduckgo_search'],
}v

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)