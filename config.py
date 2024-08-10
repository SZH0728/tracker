# -*- coding:utf-8 -*-
# AUTHOR: Sun

from json import loads
from configparser import ConfigParser


class Config(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.config = ConfigParser()
        self.config.read('config.ini')

    def __getitem__(self, item: str):
        if '.' not in item:
            return self.config[item]
        section, option = item.split('.')
        return self.get(section, option)

    def get(self, section: str, option: str):
        if section == 'base':
            if option in {'thread_pool_size', }:
                return self.config.getint(section, option)
        elif section == 'request':
            if option == 'default_headers':
                return loads(self.config.get(section, option))
            elif option in {'timeout', }:
                return self.config.getint(section, option)
        elif section == 'interval':
            return self.config.getint(section, option)
        elif section.startswith('tracker_'):
            if option == 'headers':
                return loads(self.config.get(section, option))
            elif option == 'method':
                data = self.config.get(section, option)
                data = data.replace('\\n', '\n')
                data = data.replace('\\t', '\t')
                return data
        return self.config.get(section, option)


if __name__ == '__main__':
    pass
