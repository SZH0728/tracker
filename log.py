# -*- coding:utf-8 -*-
# AUTHOR: Sun
from logging import Formatter, FileHandler, StreamHandler, INFO, DEBUG, WARNING, ERROR, CRITICAL, getLogger

from config import Config

_nameToLevel = {
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
}

logger = getLogger()
logger.setLevel(DEBUG)

config = Config()
level = config.get('logger', 'log_level')
level = _nameToLevel.get(level, INFO)

formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_path = config.get('logger', 'log_file')

if file_path:
    file_handler = FileHandler(file_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
else:
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    logger.addHandler(stream_handler)


if __name__ == '__main__':
    pass
