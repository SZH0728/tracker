# -*- coding:utf-8 -*-
# AUTHOR: Sun

from json import loads
from os.path import exists
from configparser import ConfigParser


def json(data: str):
    """
    Defines a json function that converts a string into a JSON object
    定义一个json函数，用于将字符串转换成JSON对象

    :param data: the string to be converted
                 要转换的字符串
    :return: JSON object
             JSON对象
    """
    return loads(data)


def split(data: str) -> list[str]:
    """
    Splits a comma-separated string into a list of stripped strings.
    将逗号分隔的字符串分割成去除空白字符的字符串列表。

    :param data: A comma-separated string.
                 一个逗号分隔的字符串
    :return: A list of stripped strings.
             去除空白字符的字符串列表
    """
    return [i.strip() for i in data.split(',') if i]


# Define the structure of the configuration options with their expected types.
# 定义配置选项的结构及其预期的数据类型。
STRUCTURE = {
    'base': {
        'thread_pool_size': int,
        'save_file': str,
        'tracker': split,
        'plugin': split,
    },

    'request': {
        'default_headers': json,
        'timeout': int,
    },

    'server': {
        'enable': bool,
        'port': int,
        'require_headers': json,
    },

    'interval': {
        'second': int,
        'minute': int,
        'hour': int,
        'day': int,
    },

    'logger': {
        'log_file': str,
        'log_level': str
    },

    'tracker_*': {
        'url': str,
        'method': str,
        'headers': json,
    }
}


class Config(object):
    """
    Singleton configuration class for managing application settings.
    管理应用程序设置的单例配置类。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensure only one instance of Config exists (Singleton pattern).
        确保仅存在一个 Config 实例（单例模式）。
        """
        if not cls._instance:
            # Create a new instance
            # 创建新实例
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, config: str = 'config.ini'):
        """
        Initialize the Config object with the application's configuration file.
        使用应用程序的配置文件初始化 Config 对象。

        :param config: The path to the configuration file or a string containing the configuration data.
                       配置文件的路径或包含配置数据的字符串
        """
        self.config = ConfigParser()

        # Load the configuration file if it exists, otherwise load the string as a configuration file.
        # 如果配置文件存在，则加载配置文件，否则将字符串作为配置文件加载。
        if exists(config):
            self.config.read(config, encoding='utf-8')
        else:
            self.config.read_string(config)

    def __getitem__(self, item):
        """
        Retrieve a configuration value by its key.
        通过键获取配置值。
        The access method can be config[section.option] or config[section][option]
        访问方式可以为config[section.option]或config[section][option]

        :param item: The key of the configuration value to retrieve.
                     要获取的配置值的键
        :return: The configuration value associated with the key.
                 配置键关联的值
        """
        if '.' in item:
            # Split the key into section and option
            # 将键拆分为节和选项
            section, option = item.split('.')
            return self.get(section, option)
        else:
            return OptionGetter(item, self.config)

    def __getattr__(self, item):
        """
        Proxy to __getitem__ for attribute-style access.
        代理到 __getitem__ 以实现属性风格的访问。

        :param item: The key of the configuration value to retrieve.
                     要获取的配置值的键
        :return: The configuration value associated with the key.
                 配置键关联的值
        """
        return self[item]

    def get(self, section: str, option: str):
        """
        Get a specific configuration value from a given section and option.
        从给定的节和选项获取特定的配置值。

        :param section: The section of the configuration file.
                        配置文件的节
        :param option: The option within the section.
                       节中的选项
        :return: The configuration value associated with the key.
                 配置键关联的值
        """
        if section in STRUCTURE:
            if option in STRUCTURE[section]:
                # Apply the data type defined in STRUCTURE
                # 应用 STRUCTURE 中定义的数据类型
                if isinstance(STRUCTURE[section][option], bool):
                    return self.config.getboolean(section, option)
                return STRUCTURE[section][option](self.config.get(section, option))

        elif section.startswith('tracker_'):
            # If the section starts with 'tracker_'...
            # 如果是以tracker_开头的配置...
            template = STRUCTURE['tracker_*']
            if option in template:
                # Apply the data type defined in STRUCTURE
                # 应用 STRUCTURE 中定义的数据类型
                if isinstance(template[option], bool):
                    return self.config.getboolean(section, option)
                return template[option](self.config.get(section, option))

        # Raise an exception if the key is invalid
        # 如果不符合上述条件，则抛出异常
        raise KeyError(f'Invalid config key: {section}:{option}')


class OptionGetter(object):
    """
    Helper class for getting options within a specific configuration section.
    在特定配置节内获取选项的帮助类。
    """
    def __init__(self, section: str, config: Config):
        """
        Initialize an OptionGetter with a specific section and the Config object.
        使用特定的节和 Config 对象初始化 OptionGetter。
        """
        if section not in STRUCTURE and not section.startswith('tracker_'):
            # Raise an exception if the section is invalid
            # 如果节无效，则抛出异常
            raise KeyError(f'Invalid config section: {section}')

        self.section = section
        self._config = config

    def __getitem__(self, item):
        """
        Retrieve an option value by its name, dictionary-style interface.
        通过名称获取选项值，字典风格的接口。

        :param item: The name of the option to retrieve.
                     要获取的选项的名称
        :return: The option value associated with the name.
                 选项名称关联的值
        """
        return self.get(item)

    def __getattr__(self, item):
        """
        Retrieve an option value by its name, attribute-style interface.
        通过名称获取选项值，属性风格的接口。

        :param item: The name of the option to retrieve.
                     要获取的选项的名称
        :return: The option value associated with the name.
                 选项名称关联的值
        """
        return self.get(item)

    def get(self, option: str):
        """
        Get a specific option value from the current section.
        从当前节获取特定的选项值。

        :param option: The name of the option to retrieve.
                        要获取的选项的名称
        :return: The option value associated with the name.
                 选项名称关联的值
        """
        if self.section.startswith('tracker_'):
            template = STRUCTURE['tracker_*']
        else:
            template = STRUCTURE[self.section]

        if option not in template:
            # Raise an exception if the option is invalid
            # 如果选项无效，则抛出异常
            raise KeyError(f'Invalid config option: {self.section}:{option}')

        if isinstance(template[option], bool):
            return self._config.getboolean(self.section, option)
        return template[option](self._config.get(self.section, option))


if __name__ == '__main__':
    pass
