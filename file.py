# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 管理规范 tracker 文件的原子读写边界。
@details File 持有进程内锁以协调 canonical 文件读取与原子替换；临时文件写入始终在锁外完成。
"""

from os import replace
from pathlib import Path
from threading import Lock


class File(object):
    """
    @brief 协调规范 tracker 文件的读取和原子发布。
    @details 实例持有进程内锁；读取和替换只在短暂临界区内加锁，完整暂存、同步和清理均在锁外进行。
    """

    def __init__(self, path: Path | str) -> None:
        """
        @brief 初始化规范文件边界。
        @param path 规范 tracker 文件的 canonical 路径。
        @return 无返回值；保存路径并创建进程内同步锁。
        """
        self._path = Path(path)
        self._lock = Lock()

    def read(self) -> str:
        """
        @brief 读取当前完整的规范 tracker 内容。
        @return 可用的规范文本。
        """
        with self._lock:
            content = self._path.read_text(encoding='utf-8')

        return content.strip()

    def publish(self, content: str) -> None:
        """
        @brief 原子发布完整的规范 tracker 内容。
        @details 先在固定同级临时文件中完成写入和同步，再在唯一锁保护下替换文件。
        @param content 完整的规范 tracker 文本内容。
        @return 无返回值。
        """
        temporary_path = self._path.with_name(f'{self._path.name}.tmp')
        with temporary_path.open('w', encoding='utf-8') as temporary_file:
            temporary_file.write(content)

        with self._lock:
            replace(temporary_path, self._path)


if __name__ == '__main__':
    pass
