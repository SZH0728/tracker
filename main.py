# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义应用入口层的 HTTP 响应常量。
@details 此模块未来负责依赖装配与服务生命周期；当前仅声明 HTTP 协议边界，且不创建服务器、线程或锁。
"""

from typing import Final

__all__ = [
    'ALLOW_HEADER_VALUE',
    'CONTENT_TYPE_TEXT',
    'HTTP_STATUS_METHOD_NOT_ALLOWED',
    'HTTP_STATUS_OK',
    'HTTP_STATUS_SERVICE_UNAVAILABLE',
]

HTTP_STATUS_OK: Final[int] = 200
HTTP_STATUS_SERVICE_UNAVAILABLE: Final[int] = 503
HTTP_STATUS_METHOD_NOT_ALLOWED: Final[int] = 405
CONTENT_TYPE_TEXT: Final[str] = 'text/plain; charset=utf-8'
ALLOW_HEADER_VALUE: Final[str] = 'GET, HEAD'

if __name__ == '__main__':
    pass
