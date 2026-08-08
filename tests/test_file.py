# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证规范 tracker 文件的字节常量。
@details 确保后续文件边界使用统一的 UTF-8、换行及空内容表示。
"""

from file import (
    EMPTY_TRACKER_CONTENT,
    TRACKER_CONTENT_ENCODING,
    TRACKER_LINE_SEPARATOR,
    TRACKER_TRAILING_NEWLINE,
)


def test_tracker_content_constants_define_utf8_line_protocol() -> None:
    """
    @brief 验证文件内容常量使用 UTF-8 字节行协议。
    @return 无返回值。
    """
    assert TRACKER_CONTENT_ENCODING == 'utf-8'
    assert TRACKER_LINE_SEPARATOR == b'\n'
    assert TRACKER_TRAILING_NEWLINE == b'\n'
    assert EMPTY_TRACKER_CONTENT == b''


if __name__ == '__main__':
    pass
