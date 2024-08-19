# -*- coding:utf-8 -*-
# AUTHOR: Sun

from abc import ABC, abstractmethod
from os.path import exists, isfile, join
from os import listdir
from typing import Callable
from re import compile
from logging import getLogger

from config import Config

logger = getLogger(__name__)

SCRIPT = {}

config = Config()
plugins = config.get('base', 'plugin')


class Analysis(object):
    """
    Analysis class for processing data with different methods.
    用于使用不同方法处理数据的 Analysis 类。
    """

    def __init__(self):
        """
        Initialize the Analysis object.
        初始化 Analysis 对象。
        """

        # A dictionary mapping URLs to callable methods.
        # 映射 URL 到可调用方法的字典。
        self._method: dict[str, Callable] = {}

    def load(self, url: str, method: str = None):
        """
        Load a specific method for a given URL.
        为给定的 URL 加载特定的方法。

        :param: The URL to associate the method with.
                与方法关联的 URL。
        :param: The name of the method to use.
                要使用的方法名称。
        """
        if not method:
            logger.warning(f'{url} method is empty, use default method: SPLIT()')
            # If no method is specified, use the default method, i.e., SPLIT(None)
            # 如果没有指定方法，则使用默认方法，即SPLIT(None)
            self._method[url] = Split()
            return

        if method.startswith('SPLIT'):
            # If the method starts with 'SPLIT', use the Split class with the specified keyword
            # 如果方法以 'SPLIT' 开头，则使用 Split 类，并指定关键字
            self._method[url] = Split(method)

        elif method.startswith('REGEX'):
            # If the method starts with 'REGEX', use the Regex class with the specified keyword
            # 如果方法以 'REGEX' 开头，则使用 Regex 类，并指定关键字
            self._method[url] = Regex(method)

        elif method.startswith('SCRIPT'):
            # If the method starts with 'SCRIPT', use the Script class with the specified keyword
            # 如果方法以 'SCRIPT' 开头，则使用 Script 类，并指定关键字
            self._method[url] = Script(method)

        elif method.startswith('XPATH'):
            # If the method starts with 'XPATH', judge whether to enable the plugin,
            # use the XPath class with the specified keyword
            # 如果方法以 'XPATH' 开头，判断是否启用插件，使用 XPath 类，并指定关键字
            if method.lower() not in plugins:
                logger.error(f'{method} method is not available, please enable plug-in: xpath')
                raise ValueError(f'{method} method is not available, please enable plug-in: xpath')

            self._method[url] = Xpath(method)

        elif method.startswith('CSS'):
            # If the method starts with 'CSS', judge whether to enable the plugin,
            # use the Css class with the specified keyword
            # 如果方法以 'CSS' 开头，判断是否启用插件，使用 Css 类，并指定关键字
            if method.lower() not in plugins:
                logger.error(f'{method} method is not available, please enable plug-in: css')
                raise ValueError(f'{method} method is not available, please enable plug-in: css')
            self._method[url] = CSS(method)

        else:
            # If the method is not recognized, log a warning and use the default method
            # 如果方法未被识别，则记录警告并使用默认方法
            logger.warning(f'{url} method is not recognized, use default method: SPLIT()')
            self._method[url] = Split()

    def analyze(self, url: str, data: str) -> set[str]:
        """
        Analyze data using the method associated with the given URL.
        使用与给定 URL 关联的方法分析数据。

        :param:  The URL associated with a specific analysis method.
                 与特定分析方法关联的 URL。
        :param: The data to be analyzed.
                待分析的数据。
        :return: The result of the analysis or an empty list if no method is found.
                分析的结果或如果没有找到方法则返回空列表。
        """
        if url in self._method:
            # If a method is found, log the method and use it to analyze the data
            # 如果找到方法，记录方法并使用它分析数据
            logger.info(f'{url} method is {self._method[url]}')
            return self._method[url](data)

        else:
            # If no method is found, log a warning and return an empty list
            # 如果没有找到方法，则记录警告并返回空列表
            logger.warning(f'{url} method is not found, so the data will be dropped')
            return set()


class Base(ABC):
    def __init__(self):
        self.keyword = None

    def __repr__(self):
        """
        Return a string representation of the object.
        返回对象的字符串表示形式。
        """
        return f'{self.__class__.__name__}(keyword={self.keyword})'

    def __call__(self, *args, **kwargs):
        """
        通过调用analyze方法实现相应逻辑

        :return: A list of substrings obtained after splitting the input data using the keyword.
                 使用关键字分割输入数据后得到的子字符串列表。
        """
        return self.analyze(*args, **kwargs)

    @abstractmethod
    def analyze(self, data: str) -> set[str]:
        pass


class Split(Base):
    """
    Split data by keyword
    根据关键字分割数据
    """

    def __init__(self, keyword: str = None):
        """
        Initialize the Split object.
        初始化 Split 对象。

        :param: The keyword used to split the data. Defaults to None.
                用于分割数据的关键字，默认为 None。
        """
        super().__init__()
        # Compile a regular expression pattern that matches 'SPLIT(keyword)'
        # 编译一个正则表达式模式，匹配 'SPLIT(关键字)' 的形式
        regex = compile(r'SPLIT\((.*?)\)')

        if keyword:
            # If a keyword is provided, extract it from the regex pattern
            # 如果提供了关键字，则从正则表达式模式中提取关键字
            try:
                self.keyword = regex.findall(keyword)[0]
            except IndexError:
                # Handle non-valid SPLIT methods
                # 处理非有效SPLIT方法
                logger.warning(f'{keyword} is not a valid SPLIT method, use default method: SPLIT()')
                self.keyword = None
            else:
                # Replace escaped newlines and tabs with actual newlines and tabs
                # 将转义后的换行符和制表符替换为实际的换行符和制表符
                self.keyword = self.keyword.replace('\\n', '\n')
                self.keyword = self.keyword.replace('\\t', '\t')

            if not self.keyword:
                # If no keyword is found, set it to None(Special case for SPLIT())
                # 如果没有找到关键字，则设置为 None(针对SPLIT()的情况)
                self.keyword = None
        else:
            # If no keyword is provided, set it to None
            # 如果没有提供关键字，则设置为 None
            self.keyword = None

        logger.debug(f'Split object initialized with keyword: {self.text_keyword}')

    def __repr__(self) -> str:
        """
        Return a string representation of the Split object.
        返回 Split 对象的字符串表示形式。
        """
        return f'Split(keyword={self.text_keyword})'

    @property
    def text_keyword(self):
        """
        Get the text representation of the keyword.
        获取关键字的文本表示形式。

        :return: The text representation of the keyword.
                 关键字的文本表示形式。
        """
        if self.keyword:
            text = self.keyword.replace('\n', '\\n')
            return text.replace('\t', '\\t')
        else:
            return self.keyword

    def analyze(self, data: str) -> set[str]:
        """
        Analyze and split the input data based on the keyword.
        分析并基于关键字分割输入数据。

        :param: The input data to be split.
                输入的数据，将被分割。
        :return: A list of substrings obtained after splitting the input data using the keyword.
                 使用关键字分割输入数据后得到的子字符串列表。
        """

        logger.debug(f'Splitting data using keyword: {self.text_keyword}')

        # Split the data using the keyword and filter out any empty strings
        # 使用关键字分割数据，并过滤掉任何空字符串
        return set(i.strip() for i in data.split(self.keyword) if i)


class Regex(Base):
    """
    Regex data by keyword
    根据关键字正则化数据
    """

    def __init__(self, keyword: str):
        """
        Initialize the Regex object.
        初始化 Regex 对象。

        :param: The keyword used to split the data.
                用于分割数据的关键字。
        """
        super().__init__()
        # Compile a regular expression pattern that matches 'REGEX(keyword)'
        # 编译一个正则表达式模式，匹配 'REGEX(关键字)' 的形式
        regex = compile(r'REGEX\((.*)\)')

        # Extract the keyword from the regex pattern, and compile the regular expression
        # 从正则表达式模式中提取关键字，并编译正则表达式
        try:
            self.keyword = regex.findall(keyword)[0]
        except IndexError:
            # Handle non-valid REGEX methods
            # 处理非有效REGEX方法
            logger.warning(f'{keyword} is not a valid REGEX method')
            raise ValueError(f'{keyword} is not a valid REGEX method')
        else:
            self.regex = compile(self.keyword)

        logger.debug(f'Regex object initialized with keyword: {self.keyword}')

    def analyze(self, data: str) -> set[str]:
        """
        Analyze and split the input data based on the keyword.
        使用给定的正则表达式提取数据

        :param: The input data to be split.
                输入的将被分割的数据。
        """
        logger.debug(f'Regex data using keyword: {self.keyword}')

        # Use the regular expression to find all matches in the data
        # 使用正则表达式在数据中找到所有匹配项
        return set(i.strip() for i in self.regex.findall(data) if i)


class Script(Base):
    """
    Get data by executing a script
    执行脚本获取数据
    """
    def __init__(self, keyword: str):
        """
        Initialize the Script object.
        初始化 Script 对象。

        :param keyword: The keyword used to identify the name or the path of the script.
                        关键字，用于标识脚本的名称或路径。
        """
        super().__init__()

        # Find the script keyword inside the given string
        # 在给定的字符串中找到脚本关键字
        regex = compile(r'SCRIPT\((.*)\)')
        try:
            self.keyword = regex.findall(keyword)[0]
        except IndexError:
            logger.warning(f'{keyword} is not a valid SCRIPT method')
            raise ValueError(f'{keyword} is not a valid SCRIPT method')

        if exists(self.keyword):
            # If the keyword is a valid path, create a ScriptFile object
            # 如果关键字是一个有效的路径，则创建一个 ScriptFile 对象
            self.script = ScriptFile(self.keyword)
        elif self.keyword in SCRIPT:
            # If the keyword is a valid script name, read a ScriptFile object
            # 如果关键字是一个有效的脚本名称，则读取一个 ScriptFile 对象
            self.script = SCRIPT[self.keyword]
        else:
            raise ValueError(f'{keyword} is not a valid SCRIPT method')

        self.keyword = self.script.name

    def analyze(self, data: str) -> set[str]:
        """
        Analyze the input data by executing the script's analysis function.
        通过执行脚本的 analysis 函数对输入数据进行分析。

        :param data: The input data to be analyzed.
                     输入的将被分析的数据。
        :return: A set of strings representing the analysis results.
                 表示分析结果的字符串集合。
        """
        var = {}
        # Execute the script's code in a local namespace
        # 在本地命名空间中执行脚本的代码
        exec(self.script.code, {}, var)
        # Call the 'analysis' function from the executed script and return its results
        # 调用从执行脚本中得到的 'analysis' 函数并返回其结果
        return set(var['analysis'](data))


class Xpath(Base):
    """
    Get data by Xpath
    根据 Xpath 提取数据
    """
    def __init__(self, keyword: str):
        """
        Initialize the Xpath object.
        初始化 Xpath 对象。

        :param keyword: The XPath expression used to extract data from the HTML document.
                        XPath 表达式，用于从 HTML 文档中提取数据。
                """
        super().__init__()

        regex = compile(r'XPATH\((.*)\)')

        try:
            self.keyword = regex.findall(keyword)[0]
        except IndexError:
            logger.warning(f'{keyword} is not a valid XPATH method')
            raise ValueError(f'{keyword} is not a valid XPATH method')

        logger.debug(f'Xpath object initialized with keyword: {self.keyword}')

    def analyze(self, data: str) -> set[str]:
        """
        Analyze the input HTML data using the XPath expression.
        使用 XPath 表达式分析输入的 HTML 数据。

        :param data: The HTML content to be analyzed.
                        待分析的 HTML 内容。
        :return: A set of strings representing the extracted data.
                    表示提取的数据的字符串集合。
        """
        from lxml import etree
        logger.debug(f'Xpath data using keyword: {self.keyword}')

        # Parse the HTML content
        # 解析 HTML 内容
        root = etree.HTML(data)
        # Extract data using the XPath expression
        # 使用 XPath 表达式提取数据
        return set(i.strip() for i in root.xpath(self.keyword) if i)


class CSS(Base):
    """
    Get data by CSS selector
    根据 CSS 选择器提取数据
    """
    def __init__(self, keyword: str):
        """
        Initialize the CSS object.
        初始化 CSS 对象。

        :param keyword: The CSS selector used to extract data from the HTML document.
                        CSS 选择器，用于从 HTML 文档中提取数据。
        """
        super().__init__()

        # Compile the regular expression to find the CSS keyword
        # 编译正则表达式以找到 CSS 关键字
        regex = compile(r'CSS\((.*)\)')

        try:
            self.keyword = regex.findall(keyword)[0]
        except IndexError:
            logger.warning(f'{keyword} is not a valid CSS method')
            raise ValueError(f'{keyword} is not a valid CSS method')

        logger.debug(f'CSS object initialized with keyword: {self.keyword}')

    def analyze(self, data: str) -> set[str]:
        """
        Analyze the input HTML data using the CSS selector.
        使用 CSS 选择器分析输入的 HTML 数据。

        :param data: The HTML content to be analyzed.
                        待分析的 HTML 内容。
        :return: A set of strings representing the extracted data.
                    表示提取的数据的字符串集合。
        """
        from pyquery import PyQuery
        logger.debug(f'CSS data using keyword: {self.keyword}')

        # Create a PyQuery object from the HTML content
        # 从 HTML 内容创建 PyQuery 对象
        doc = PyQuery(data)
        # Extract data using the CSS selector
        # 使用 CSS 选择器提取数据
        return set(i.strip() for i in doc(self.keyword).items() if i)

class ScriptFile(object):
    """
    A class to represent a script file.
    用于表示脚本文件的类。
    """
    def __init__(self, file_path: str):
        """
        Initialize the ScriptFile object.
        初始化 ScriptFile 对象。

        :param file_path: The path to the script file.
                          脚本文件的路径。
        """
        if not exists(file_path):
            raise FileNotFoundError(f'{file_path} is not found')

        self._file_path = file_path
        self._code = []
        comment_description_regex = compile(r'^#\s*@(.*?)\s*:\s*(.*)$')

        with open(self._file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if not line:
                    # Skip empty lines
                    # 跳过空行
                    continue

                if line.startswith('#'):
                    # Extract metadata from comments
                    # 从注释中提取元数据
                    match = comment_description_regex.match(line)
                    if match:
                        key, value = match.groups()
                        self._data[key] = value
                else:
                    # Add non-comment lines to the script code
                    # 将非注释行添加到脚本代码中
                    self._code.append(line)

    def __getitem__(self, item):
        """
        Retrieve metadata by key.
        通过key获取元数据。
        """
        return self._data.get(item)

    def __getattr__(self, item):
        """
        Retrieve metadata as attributes.
        获取元数据作为属性。
        """
        return self._data.get(item)

    @property
    def file_path(self):
        """
        Get the file path of the script.
        获取脚本的文件路径。
        """
        return self._file_path

    @property
    def code(self):
        """
        Get the compiled code of the script.
        获取脚本的编译代码。
        """
        return '\n'.join(self._code)

    def get(self, key, default=None):
        """
        Get metadata by key with a default value.
        通过key获取元数据

        :param key: The key of the metadata.
                    元数据的key
        :param default: The default value of the metadata.
                        元数据的默认值
        :return: The metadata value.
                 元数据值
        """
        return self._data.get(key, default)


# Load all script files from the './script' directory
# 从 './script' 目录加载所有脚本文件
for filename in listdir('./script'):
    filepath = join('./script', filename)
    if isfile(filepath):
        # Create a ScriptFile object
        # 创建一个 ScriptFile 对象
        file = ScriptFile(filepath)
        SCRIPT[file.name] = file

if __name__ == '__main__':
    pass
