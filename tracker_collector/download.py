# -*- coding:utf-8 -*-
# AUTHOR: Sun

from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from urllib.request import build_opener, Request
from logging import getLogger

logger = getLogger(__name__)


class Downloader:
    """
    A simple multithreading downloader class for concurrent HTTP requests.
    一个简单的多线程下载器类，用于并发地发送HTTP请求并获取响应。
    """

    def __init__(self, default_headers: dict = None, timeout: int = 8, workers: int = 8):
        """
        Initialize Downloader object.
        初始化Downloader对象。

        :param default_headers: 默认的HTTP头部信息字典。
                                Default HTTP header information dictionary.
        :param timeout: 每个请求的超时时间（秒）。
                        Timeout for each request (in seconds).
        :param workers: 线程池中的线程数量。
                        Thread pool size.
        """
        self.timeout = timeout

        # Use provided default headers or empty dictionary
        # 使用提供的默认头部或空字典
        self.default_headers = default_headers if default_headers else {}

        # Create thread pool executor
        # 创建线程池执行器
        self._executor = ThreadPoolExecutor(max_workers=workers)

        # Construct URL opener
        # 构建URL打开器
        self._opener = build_opener()

        # Create a mapping from Future to Request object
        # 创建一个Future到Request对象的映射
        self._target_requests: dict[Future, Request] = {}

    def get(self, *args: (str | Request), headers: dict = None) -> list[Future]:
        """
        Send GET requests and return a list of Future objects.
        发送GET请求，并返回Future对象列表。

        :param args: 可以是URL字符串或Request对象。
                     A list of URL strings or Request objects.
        :param headers: 要添加到每个请求的额外头部信息。
                        Additional headers to add to each request.
        :return: 一个Future对象列表，代表异步任务。
                 A list of Future objects representing asynchronous tasks.
        """
        if headers is None:
            headers = {}

        # Update default headers
        # 更新默认头部
        headers.update(self.default_headers)
        logger.debug(f'Default headers: {headers}')
        requests = []

        # Construct Request objects and add headers
        # 根据输入构建Request对象并添加头部信息
        for item in args:
            if isinstance(item, Request):
                item.method = 'GET'
                for key, value in headers.items():
                    item.add_header(key, value)

            else:
                item = Request(item, method='GET', headers=headers)

            logger.debug(f'Construct request {item}')
            requests.append(item)

        futures = []
        for request in requests:
            logger.debug(f'Submit request {request} to executor')

            # Submit task to executor
            # 提交任务到线程池
            future = self._executor.submit(self._load_request, request)
            futures.append(future)

            self._target_requests[future] = request

        return futures

    def complete(self) -> list[tuple[str, Request]]:
        """
        Get completed requests and their results.
        获取已完成的请求及其结果。

        :return: 一个生成器，每次迭代返回一个元组，包含响应内容和对应的Request对象。
                 A generator that yields a tuple for each completed request,
        """
        for future in as_completed(self._target_requests):
            logger.debug(f'Get response from {self._target_requests[future]}')
            # Get result from future
            # 从Future中获取结果
            yield future.result(), self._target_requests.pop(future)

    def _load_request(self, request: Request):
        """
        Load a single request and return the response content.
        加载单个请求并返回响应内容。

        :param request: 要加载的Request对象。
                        The Request object to load.
        :return: 响应的内容或在出现错误时返回异常对象。
                 The response content or an exception object on failure.
        """
        try:
            logger.info(f'Start to load request: {request}')

            # Open request and read response
            # 打开请求并读取响应
            with self._opener.open(request, timeout=self.timeout) as response:
                response = response.read().decode('utf-8')
                logger.debug(f'Load request {request} successfully')
                return response

        except Exception as e:
            logger.error(f'Failed to load request: {request} due to {e}')
            return e


if __name__ == '__main__':
    pass
