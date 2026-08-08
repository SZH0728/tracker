# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证 HTTP 入口协议常量。
@details 确保后续 HTTP 处理器使用设计文档规定的状态码和响应头。
"""

from main import (
    ALLOW_HEADER_VALUE,
    CONTENT_TYPE_TEXT,
    HTTP_STATUS_METHOD_NOT_ALLOWED,
    HTTP_STATUS_OK,
    HTTP_STATUS_SERVICE_UNAVAILABLE,
)


def test_http_protocol_constants_match_design_contract() -> None:
    """
    @brief 验证入口层公开的 HTTP 协议常量。
    @return 无返回值。
    """
    assert HTTP_STATUS_OK == 200
    assert HTTP_STATUS_SERVICE_UNAVAILABLE == 503
    assert HTTP_STATUS_METHOD_NOT_ALLOWED == 405
    assert CONTENT_TYPE_TEXT == 'text/plain; charset=utf-8'
    assert ALLOW_HEADER_VALUE == 'GET, HEAD'


if __name__ == '__main__':
    pass
