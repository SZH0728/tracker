# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义规范 tracker 列表文件的字节不变式。
@details 后续 File 边界负责读写这些字节；本模块不创建锁，也不执行文件系统操作。
"""

from typing import Final

__all__ = [
    'EMPTY_TRACKER_CONTENT',
    'TRACKER_CONTENT_ENCODING',
    'TRACKER_LINE_SEPARATOR',
    'TRACKER_TRAILING_NEWLINE',
]

TRACKER_CONTENT_ENCODING: Final[str] = 'utf-8'
TRACKER_LINE_SEPARATOR: Final[bytes] = b'\n'
TRACKER_TRAILING_NEWLINE: Final[bytes] = b'\n'
EMPTY_TRACKER_CONTENT: Final[bytes] = b''

if __name__ == '__main__':
    pass
