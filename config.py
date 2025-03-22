import configparser

CONFIG = None


def get_config():
    global CONFIG
    if CONFIG:
        return CONFIG
    config = configparser.ConfigParser()
    config.read("conf.ini")
    return config
