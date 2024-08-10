# -*- coding:utf-8 -*-
# AUTHOR: Sun

from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from urllib.request import build_opener, Request
from logging import getLogger

logger = getLogger(__name__)


class Downloader(object):
    def __init__(self, default_headers: dict = None, timeout: int = 8, workers: int = 8):
        self.timeout = timeout
        self.default_headers = default_headers if default_headers else {}

        self._executor = ThreadPoolExecutor(workers)
        self._opener = build_opener()

        self._target_requests: dict[Future, Request] = {}

    def get(self, *args: str | Request, headers: dict = None):
        if headers is None:
            headers = {}

        headers.update(self.default_headers)
        requests = []

        for i in args:
            if isinstance(i, Request):
                i.method = 'GET'
                for key, value in headers.items():
                    i.add_header(key, value)
            else:
                i = Request(i, method='GET', headers=headers)
            requests.append(i)

        futures: list[Future] = []
        for i in requests:
            logger.debug(f'Submit request {i} to executor')
            future = self._executor.submit(self._load_request, i)
            futures.append(future)
            self._target_requests[future] = i
        return futures

    def complete(self):
        for future in as_completed(self._target_requests):
            logger.debug(f'Get response from {self._target_requests[future]}')
            yield future.result(), self._target_requests[future]

    def _load_request(self, request: Request):
        try:
            logger.debug(f'Start to load request: {request}')
            with self._opener.open(request, timeout=self.timeout) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f'Failed to load request: {request} due to {e}')
            return e


if __name__ == '__main__':
    pass
