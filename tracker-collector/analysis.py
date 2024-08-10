# -*- coding:utf-8 -*-
# AUTHOR: Sun

from typing import Callable
from re import compile
from logging import getLogger

logger = getLogger(__name__)


class Analysis(object):
    def __init__(self):
        self._method: dict[str, Callable] = {}

    def load(self, url: str, method: str):
        if not method:
            method = 'SPLIT()'
            logger.warning(f'{url} method is empty, use default method: {method}')

        if method.startswith('SPLIT'):
            self._method[url] = self._split(method)

    def analyze(self, url: str, data: str):
        if url in self._method:
            logger.info(f'{url} method is {self._method[url]}')
            return self._method[url](data)
        else:
            logger.warning(f'{url} method is not found, so the data will be dropped')
            return []

    @staticmethod
    def _split(expression: str):
        regex = compile(r'SPLIT\((.*?)\)')
        keyword = regex.findall(expression)
        keyword = keyword[0] if keyword else None

        def split(data: str):
            return [i for i in data.split(keyword) if i]

        return split


if __name__ == '__main__':
    pass
