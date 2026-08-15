# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 运行有序 tracker 采集与发布流水线。
@details Assembler 在唯一工作线程中消费已装配的数据源、解析器、请求器和文件边界，不创建跨线程状态。
"""

from logging import getLogger
from threading import Event
from time import sleep

from data import RawConfig
from error import ParserError
from file import File
from parser import ParserFactory
from requester import Requester

logger = getLogger(__name__)


class Assembler(object):
    """
    @brief 聚合成功数据源并发布规范 tracker 内容。
    @details 每轮只保留局部采集结果；所有来源失败时保持现有文件，至少一个来源成功时发布本轮结果。
    """

    def __init__(self, config: RawConfig, file: File, parser: ParserFactory) -> None:
        """
        @brief 初始化刷新流水线。
        @param config 包含有序数据源与刷新间隔的原始配置。
        @param file 发布规范文本内容的文件边界。
        @param parser 按来源引用解析响应解析器的工厂。
        @return 无返回值；保存已注入依赖并创建请求边界。
        @throws ValueError 当刷新间隔不为正整数时。
        """
        if config.global_config.refresh_interval <= 0:
            raise ValueError('刷新间隔必须为正整数。')

        self._config: RawConfig = config
        self._file: File = file
        self._requester: Requester = Requester()
        self._parser: ParserFactory = parser

    def run(self, stop_event: Event | None = None) -> None:
        """
        @brief 持续执行 tracker 刷新周期。
        @details 启动后立即刷新；传入停止事件时可在等待周期内退出。
        @return 无返回值；在调用线程中持续运行。
        """
        while True:
            try:
                self.refresh_once()
                if stop_event is None:
                    sleep(self._config.global_config.refresh_interval)
                elif stop_event.wait(self._config.global_config.refresh_interval):
                    return
            except KeyboardInterrupt:
                logger.info('收到中断信号，停止 tracker 刷新。')

    def refresh_once(self) -> None:
        """
        @brief 执行一次完整的 tracker 刷新。
        @details 按配置顺序获取并解析来源，稳定去重本轮 URL；全部来源失败时保留现有文件，成功来源为空时发布空内容。
        @return 无返回值；成功来源存在时发布本轮规范内容。
        """
        urls: list[str] = []
        successful_sources = 0

        for source in self._config.tracker_sources:
            response = self._requester.fetch(source)
            if response is None:
                logger.warning(f'获取数据源失败，跳过解析：{source.name}')
                continue

            try:
                parser = self._parser.resolve_parser(source.parser)
                parsed_urls = parser(response)
            except ParserError as error:
                logger.exception(f'解析数据源失败，跳过发布结果：{source.name} ({error})')
                continue

            successful_sources += 1
            urls.extend(parsed_urls)

        if successful_sources == 0:
            logger.warning('本轮没有成功数据源，保留现有 tracker 文件。')
            return

        unique_urls: set[str] = set(urls)
        content = '' if not urls else '\n'.join(unique_urls)
        self._file.publish(content)


if __name__ == '__main__':
    pass
