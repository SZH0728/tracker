# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 提供上游 HTTP 获取能力。
@details Requester 消费已校验的数据源记录，通过 requests 执行默认重定向与有限重试；成功时完整读取响应并关闭传输资源后返回原生响应。
"""

from logging import getLogger
from time import sleep
from typing import Self

from requests import ConnectionError, RequestException, Response, Session, Timeout

from data import RawTrackerSource

logger = getLogger(__name__)


class Requester(object):
    """
    @brief 获取上游 HTTP 响应。
    @details 该类不读取配置、不持有锁且不调用解析器；fetch 使用来源级超时、重试次数和重试间隔，并将 URL 与重定向处理委托给 requests。
    """

    def __init__(self) -> None:
        """
        @brief 初始化共享同步请求会话。
        @return 无返回值；创建供多次获取复用的请求会话。
        """
        self._session = Session()

    def __enter__(self) -> Self:
        """
        @brief 进入请求器上下文。
        @return 当前请求器实例。
        """
        return self

    def __exit__(self, exception_type: type[BaseException] | None, exception: BaseException | None, traceback: object | None) -> None:
        """
        @brief 退出请求器上下文并释放会话资源。
        @param exception_type 上下文内异常的类型
        @param exception 上下文内抛出的异常
        @param traceback 上下文内异常的回溯信息
        @return 无返回值；关闭共享请求会话。
        """
        self.close()

    def close(self) -> None:
        """
        @brief 关闭共享请求会话。
        @return 无返回值；释放会话持有的连接池资源。
        """
        self._session.close()

    def fetch(self, source: RawTrackerSource) -> Response | None:
        """
        @brief 获取一个数据源的完整 HTTP 响应。
        @details 仅对连接错误、超时和服务端错误进行有界重试，成功时返回已读取内容且已关闭底层传输的原生 requests.Response。
        @param source 已由配置边界校验的数据源记录
        @return 满足传输策略的原生响应；预期传输失败时返回 None。
        """
        max_attempts = source.retry + 1
        for attempt in range(1, max_attempts + 1):
            logger.info(f'开始获取数据源 {source.name}，第 {attempt}/{max_attempts} 次尝试。')
            response, can_retry = self._fetch_once(source)

            if response is not None:
                logger.info(f'成功获取数据源 {source.name}，第 {attempt}/{max_attempts} 次尝试。')
                return response

            if not can_retry or attempt == max_attempts:
                return None

            sleep(source.retry_interval)

        return None

    def _fetch_once(self, source: RawTrackerSource) -> tuple[Response | None, bool]:
        try:
            response = self._session.get(
                source.url,
                headers=dict(source.headers),
                timeout=source.request_timeout,
            )
        except (ConnectionError, Timeout) as e:
            logger.warning(f"获取数据源 {source.url} 失败: 网络连接或超时 ({type(e).__name__}: {e})")
            return None, True
        except RequestException as e:
            logger.exception(f"获取数据源 {source.url} 失败: 遇到不可恢复的请求异常 ({type(e).__name__}: {e})")
            return None, False

        if 500 <= response.status_code <= 599:
            logger.warning(f"获取数据源 {source.url} 失败: 服务端响应异常 (HTTP {response.status_code})")
            return None, True

        if 400 <= response.status_code <= 499:
            logger.error(f"获取数据源 {source.url} 失败: 客户端请求错误 (HTTP {response.status_code})")
            return None, False

        return response, False


if __name__ == '__main__':
    pass
