# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义上游 HTTP 获取结果的不可变契约。
@details 后续 Requester 仅以此记录向解析层传递安全的成功响应元数据或经清理的预期失败信息。
"""

from dataclasses import dataclass
from enum import StrEnum

__all__ = ['FetchFailureKind', 'FetchResult']


class FetchFailureKind(StrEnum):
    """
    @brief 枚举可预期的上游获取失败类别。
    @details 枚举值供装配器记录稳定诊断，且不包含上游响应体或敏感请求头。
    """

    NETWORK = 'network'
    TIMEOUT = 'timeout'
    HTTP = 'http'
    REDIRECT = 'redirect'
    RESPONSE_TOO_LARGE = 'response-too-large'


@dataclass(frozen=True, slots=True)
class FetchResult(object):
    """
    @brief 表示一次上游获取的成功响应或预期失败。
    @details 成功记录拥有完整的安全响应视图；失败记录绝不保留原始响应体。
    """

    attempts: int  # 已执行的请求次数
    body: bytes | None  # 成功响应的原始字节
    content_type: str | None  # 已规范化的响应内容类型
    failure_kind: FetchFailureKind | None  # 失败的稳定类别
    failure_message: str | None  # 已清理的失败说明
    final_url: str | None  # 最终响应地址
    original_url: str  # 配置的初始请求地址
    status_code: int | None  # 上游 HTTP 状态码

    def __post_init__(self) -> None:
        """
        @brief 验证成功与失败记录的互斥字段。
        @details 成功结果必须完整提供解析器所需数据，失败结果不得携带响应体。
        @throws TypeError 当 attempts 不是整数或 body 不是字节时。
        @throws ValueError 当结果字段组合不符合成功或失败契约时。
        """
        if not isinstance(self.attempts, int):
            raise TypeError(f'attempts 必须为 int，实际类型为：{type(self.attempts).__name__}')
        if self.attempts < 1:
            raise ValueError(f'attempts 必须大于等于 1，实际值为：{self.attempts}')
        if self.body is not None and not isinstance(self.body, bytes):
            raise TypeError(f'body 必须为 bytes 或 None，实际类型为：{type(self.body).__name__}')

        is_success = self.failure_kind is None and self.failure_message is None
        if is_success:
            if self.body is None or self.final_url is None or self.status_code is None:
                raise ValueError('成功结果必须包含 body、final_url 和 status_code')
            return

        if self.failure_kind is None or self.failure_message is None:
            raise ValueError('失败结果必须同时包含 failure_kind 和 failure_message')
        if self.body is not None:
            raise ValueError('失败结果不得包含响应 body')

    @property
    def is_success(self) -> bool:
        """
        @brief 判断获取是否成功。
        @return 成功结果返回 True，预期失败结果返回 False。
        """
        return self.failure_kind is None


if __name__ == '__main__':
    pass
