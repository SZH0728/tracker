# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import (Formatter, FileHandler, StreamHandler, getLogger,
                     INFO, DEBUG, WARNING, ERROR, CRITICAL, )

from config import Config

# Mapping of log level names to their corresponding integer values.
# 将日志级别名称映射为对应的整数值
_nameToLevel = {
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
}


def read_config() -> tuple[str, str]:
    """
    Reads the configuration settings for logging.
    读取日志配置

    :return: A tuple containing the log level and log file path as configured.
             返回一个包含日志级别和日志文件路径的元组。
    """
    config = Config()
    log_level = config.get('logger', 'log_level')
    log_file = config.get('logger', 'log_file')
    return log_level, log_file


class LogConfig(object):
    """
    Configuration class for setting up logging.
    配置日志设置
    """
    def __init__(self, log_level: str | int = 'INFO', log_file: str = None):
        """
        Initializes the LogConfig with a default log level and log file path.
        初始化LogConfig，默认日志级别和日志文件路径

        :param log_level: The initial log level, defaults to 'INFO'.
                          最初日志级别，默认为INFO
        :param log_file: The path to the log file, defaults to None, indicating output to the console.
                         日志文件路径，默认为None，即输出到控制台
        """
        self.logger = getLogger()

        # Set the log level property based on the input or default value.
        # 设置日志级别属性，根据输入或默认值。
        self._set_log_level_property(log_level)
        self._log_file = log_file
        self._formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.load_log_config()

    def _set_log_level_property(self, log_level):
        """
        Sets the log level property based on the input string or integer.
        根据输入字符串或整数设置日志级别属性。

        :param log_level: The log level as a string or integer.
                          日志级别字符串或整数
        """
        if isinstance(log_level, str):
            self._log_level = _nameToLevel.get(log_level, INFO)
        else:
            self._log_level = log_level

    def set_log_level(self):
        """
        Sets the log level for the logger.
        设置日志级别
        """
        self.logger.setLevel(self._log_level)

    def set_log_file(self):
        """
        Configures the log file handler or stream handler based on the log file path.
        根据日志文件路径配置日志文件处理器或流处理器。
        """
        if self._log_file:
            file_handler = FileHandler(self._log_file)
            file_handler.setFormatter(self._formatter)
            file_handler.setLevel(self._log_level)
            self.logger.addHandler(file_handler)
        else:
            stream_handler = StreamHandler()
            stream_handler.setFormatter(self._formatter)
            stream_handler.setLevel(self._log_level)
            self.logger.addHandler(stream_handler)

    def load_log_config(self):
        """
        Loads the log configuration by setting the log level and configuring the log file.
        加载日志配置，设置日志级别和配置日志文件
        """
        self.set_log_level()
        self.set_log_file()

    @property
    def log_level(self):
        """
        Gets the current log level.
        获取当前日志级别

        :return: The current log level.
                 当前日志级别
        """
        return self._log_level

    @log_level.setter
    def log_level(self, log_level: str | int):
        """
        Sets the log level and reloads the log configuration.
        设置日志级别并重新加载日志配置。

        :param log_level: The new log level as a string or integer.
                          新日志级别字符串或整数
        """
        self._set_log_level_property(log_level)
        self.load_log_config()

    @property
    def log_file(self):
        """
        Gets the current log file path.
        获取当前日志文件路径

        :return: The path to the log file.
                 日志文件路径
        """
        return self._log_file

    @log_file.setter
    def log_file(self, log_file: str):
        """
        Sets the log file path and reloads the log configuration.
        设置日志文件路径并重新加载日志配置。

        :param log_file: The new path to the log file.
                         新日志文件路径
        """
        self._log_file = log_file
        self.load_log_config()

    @property
    def formatter(self):
        """
        Gets the current log message formatter.
        获取当前日志消息格式化器

        :return: The log message formatter.
                 日志消息格式化器
        """
        return self._formatter

    @formatter.setter
    def formatter(self, formatter: Formatter):
        """
        Sets the log message formatter and reloads the log configuration.
        设置日志消息格式化器并重新加载日志配置。

        :param formatter: The new log message formatter.
                          新的日志消息格式化器
        """
        self._formatter = formatter
        self.load_log_config()


if __name__ == '__main__':
    pass
