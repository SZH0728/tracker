# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义并加载配置边界的原始不可变记录。
@details Config 是唯一使用 ConfigParser 的边界，负责将 INI 输入校验并转换为原始记录；不保留解析器实例，也不解释解析器或 tracker 业务语义。
"""

from configparser import RawConfigParser, SectionProxy
from json import loads, JSONDecodeError
from pathlib import Path
from re import compile

from data import RawConfig, RawGlobalConfig, RawParserSection, RawTrackerSource
from error import ConfigError

GLOBAL_SECTION = 'global'
GLOBAL_KEYS = frozenset({'port', 'output_file', 'refresh_interval'})

TRACKER_PREFIX = 'tracker.'
PARSER_PREFIX = 'parser.'

TRACKER_REQUIRED_KEYS = frozenset({'url', 'request_timeout', 'retry', 'retry_interval', 'parser'})
TRACKER_KEYS = TRACKER_REQUIRED_KEYS | frozenset({'header'})
PARSER_KEYS = frozenset({'base'})

IDENTIFIER_PATTERN = compile(r'[A-Za-z0-9][A-Za-z0-9_.-]*\Z')


class Config(object):
    """
    @brief 管理可重新加载的 INI 配置。
    @details path 可由调用方修改；只有调用 reload 后才读取当前路径。加载失败会保留最后一次成功的原始配置快照。
    """

    def __init__(self, path: Path | str) -> None:
        """
        @brief 初始化配置并立即加载。
        @param path INI 配置文件路径
        @throws ConfigError 当文件无法读取、INI 格式无效或通用字段不符合约束时
        """
        self._path: Path = Path(path)
        self._config: RawConfig | None = None

        self.reload()

    @property
    def config(self) -> RawConfig:
        """
        @brief 获取最近一次成功加载的原始配置。
        @return 不可变的原始配置快照
        """
        if self._config is None:
            raise RuntimeError('配置尚未成功加载。')
        return self._config

    @property
    def path(self) -> Path:
        """
        @brief 获取下次加载使用的配置文件路径。
        @details 仅读取当前保存的路径，不执行文件 I/O 或重新加载。
        @return 当前配置文件路径
        """
        return self._path

    @path.setter
    def path(self, path: Path | str) -> None:
        """
        @brief 更新下次加载使用的配置文件路径。
        @details 仅更新待加载路径，不自动读取文件，也不替换当前成功的配置快照。
        @param path 新的 INI 配置文件路径
        @return 无返回值；更新内部待加载路径
        """
        self._path = Path(path)

    def reload(self, path: str | Path | None = None) -> None:
        """
        @brief 从当前配置路径重新加载配置。
        @details 完整校验成功后才替换配置快照，失败时保留上一次成功加载的配置。
        @throws ConfigError 当文件无法读取、INI 格式无效或通用字段不符合约束时
        """
        if path is not None:
            self.path = path

        parser = RawConfigParser(strict=True)

        try:
            parser.read(self.path, encoding='utf-8')
        except Exception as error:
            raise ConfigError(f'无法读取或解析配置文件 {self.path}: {error}') from error

        self._raise_for_defaults(parser)
        self._raise_for_sections(parser)

        global_config = self._load_global_config(parser)
        tracker_sources, parser_sections = self._load_sections(parser)
        self._config = RawConfig(global_config, tracker_sources, parser_sections)

    def _raise_for_defaults(self, parser: RawConfigParser) -> None:
        """
        @brief 拒绝使用 DEFAULT 配置节。
        @details 默认节会向其他节隐式注入字段，破坏各节的显式键约束。
        @param parser 已读取的 INI 解析器
        @return 无返回值；默认节符合约束时直接结束
        @throws ConfigError 当配置包含 DEFAULT 节的默认键时
        """
        if parser.defaults():
            raise ConfigError(f'配置文件 {self.path} 不允许使用 DEFAULT 节。')


    def _raise_for_sections(self, parser: RawConfigParser) -> None:
        """
        @brief 校验配置节的结构与允许前缀。
        @details 必须存在 global 节，其余节仅可使用 tracker. 或 parser. 前缀。
        @param parser 已读取的 INI 解析器
        @return 无返回值；节结构符合约束时直接结束
        @throws ConfigError 当缺少 global 节或存在不支持的配置节时
        """
        if GLOBAL_SECTION not in parser:
            raise ConfigError(f'配置文件 {self.path} 缺少必需的 [{GLOBAL_SECTION}] 节。')

        for section_name in parser.sections():
            if section_name == GLOBAL_SECTION:
                continue

            if section_name.startswith(TRACKER_PREFIX):
                self._raise_for_identifier(section_name, TRACKER_PREFIX)
                continue

            if section_name.startswith(PARSER_PREFIX):
                self._raise_for_identifier(section_name, PARSER_PREFIX)
                continue

            raise ConfigError(f'配置文件 {self.path} 包含不支持的配置节 [{section_name}]。')

    def _raise_for_identifier(self, section_name: str, prefix: str) -> None:
        """
        @brief 校验带前缀配置节的别名。
        @details 别名必须非空，且仅包含字母、数字、下划线、连字符与点号。
        @param section_name 完整配置节名称
        @param prefix 已确认匹配的配置节前缀
        @return 无返回值；别名符合约束时直接结束
        @throws ConfigError 当配置节缺少别名或别名格式无效时
        """
        identifier = section_name.removeprefix(prefix)
        if not IDENTIFIER_PATTERN.fullmatch(identifier):
            raise ConfigError(f'配置文件 {self.path} 的配置节 [{section_name}] 缺少或包含无效别名。')

    def _load_global_config(self, parser: RawConfigParser) -> RawGlobalConfig:
        """
        @brief 加载并校验全局服务配置。
        @details 仅转换全局通用字段，不在此处触发运行时服务行为。
        @param parser 已完成节结构校验的 INI 解析器
        @return 不可变的全局原始配置
        @throws ConfigError 当全局键缺失、未知或值不符合约束时
        """
        section: SectionProxy = parser[GLOBAL_SECTION]
        self._raise_for_keys(section.name, section, GLOBAL_KEYS, GLOBAL_KEYS)

        return RawGlobalConfig(
            port=self._parse_integer(section, 'port'),
            output_file=self._parse_text(section, 'output_file'),
            refresh_interval=self._parse_integer(section, 'refresh_interval'),
        )

    def _load_sections(self, parser: RawConfigParser) -> tuple[tuple[RawTrackerSource, ...], tuple[RawParserSection, ...]]:
        """
        @brief 按声明顺序加载 tracker 与 parser 配置节。
        @details 分别构建两类原始记录，同时保留各自于 INI 中的声明顺序。
        @param parser 已完成节结构校验的 INI 解析器
        @return 有序的 tracker 来源元组与 parser 配置节元组
        @throws ConfigError 当任一配置节的通用字段无效时
        """
        tracker_sources: list[RawTrackerSource] = []
        parser_sections: list[RawParserSection] = []

        for section_name in parser.sections():
            if section_name.startswith(TRACKER_PREFIX):
                tracker_sources.append(self._load_tracker_section(parser[section_name]))
            elif section_name.startswith(PARSER_PREFIX):
                parser_sections.append(self._load_parser_section(parser[section_name]))

        return tuple(tracker_sources), tuple(parser_sections)

    def _load_tracker_section(self, section: SectionProxy) -> RawTrackerSource:
        """
        @brief 加载单个 tracker 数据源配置节。
        @details 仅校验通用字段并保留解析器引用文本，不解释请求或解析器业务语义。
        @param section 已读取的 tracker 配置节
        @return 不可变的 tracker 原始来源记录
        @throws ConfigError 当必需键、允许键或字段值不符合约束时
        """
        self._raise_for_keys(section.name, section, TRACKER_REQUIRED_KEYS, TRACKER_KEYS)
        return RawTrackerSource(
            name=section.name.removeprefix(TRACKER_PREFIX),
            url=self._parse_text(section, 'url'),
            headers=self._parse_headers(section, 'header'),
            request_timeout=self._parse_integer(section, 'request_timeout'),
            retry=self._parse_integer(section, 'retry'),
            retry_interval=self._parse_integer(section, 'retry_interval'),
            parser=self._parse_text(section, 'parser'),
        )

    def _load_parser_section(self, section: SectionProxy) -> RawParserSection:
        """
        @brief 加载单个 parser 配置节。
        @details 保留 base 和其他选项的原始字符串，由 parser 模块解释其语义。
        @param section 已读取的 parser 配置节
        @return 不可变的 parser 原始配置节记录
        @throws ConfigError 当缺少 base 或 base 为空时
        """
        self._raise_for_keys(section.name, section, PARSER_KEYS, None)
        return RawParserSection(
            name=section.name.removeprefix(PARSER_PREFIX),
            base=self._parse_text(section, 'base'),
            options=tuple((key, value) for key, value in section.items() if key != 'base'),
        )

    def _raise_for_keys(self, section_name: str, section: SectionProxy, required_keys: frozenset[str], allowed_keys: frozenset[str] | None) -> None:
        """
        @brief 校验配置节的必需键与允许键。
        @details 先拒绝缺失的必需键；allowed_keys 为 None 时允许额外选项供下游模块解释。
        @param section_name 用于错误上下文的配置节名称
        @param section 待校验的配置节
        @param required_keys 必须存在的键集合
        @param allowed_keys 允许存在的键集合；None 表示不限制未知键
        @return 无返回值；键集合符合约束时直接结束
        @throws ConfigError 当存在缺失必需键或未知键时
        """
        keys = set(section.keys())

        missing_keys = required_keys - keys
        if missing_keys:
            joined_keys = ', '.join(sorted(missing_keys))
            raise ConfigError(f'配置文件 {self.path} 的 [{section_name}] 节缺少必需键 {joined_keys}。')

        if allowed_keys is None:
            return

        unknown_keys = keys - allowed_keys
        if unknown_keys:
            joined_keys = ', '.join(sorted(unknown_keys))
            raise ConfigError(f'配置文件 {self.path} 的 [{section_name}] 节包含未知键 {joined_keys}。')

    def _parse_text(self, section_proxy: SectionProxy, key: str) -> str:
        """
        @brief 读取非空文本配置值。
        @details 缺失、空字符串与仅包含空白字符的值均不属于有效文本。
        @param section_proxy 包含目标键的配置节
        @param key 待读取的配置键
        @return 保留原始内容的非空文本值
        @throws ConfigError 当配置键缺失或文本为空时
        """
        value: str | None = section_proxy.get(key)

        if value is None or not value.strip():
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 {key} 不能为空。')

        return value

    def _parse_integer(self, section_proxy: SectionProxy, key: str, allow_negative: bool = False) -> int:
        """
        @brief 读取整数配置值。
        @details 默认拒绝负数；允许负数时仅保留标准库的整数转换语义。
        @param section_proxy 包含目标键的配置节
        @param key 待读取的配置键
        @param allow_negative 是否允许负整数，默认不允许
        @return 已转换的整数值
        @throws ConfigError 当值缺失或在不允许负数时为负数
        """
        try:
            value: int | None = section_proxy.getint(key)
        except ValueError as error:
            raise ConfigError from error

        if value is None:
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 {key} 必须为非负十进制整数。')

        if not allow_negative and value < 0:
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 {key} 必须为非负十进制整数。')

        return value

    def _parse_float(self, section_proxy: SectionProxy, key: str, allow_negative: bool = False) -> float:
        """
        @brief 读取浮点数配置值。
        @details 默认拒绝负数；允许负数时仅保留标准库的浮点转换语义。
        @param section_proxy 包含目标键的配置节
        @param key 待读取的配置键
        @param allow_negative 是否允许负浮点数，默认不允许
        @return 已转换的浮点数值
        @throws ConfigError 当值缺失或在不允许负数时为负数
        """
        try:
            value: float | int | None = section_proxy.getfloat(key)
        except ValueError as error:
            raise ConfigError from error

        if value is None:
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 {key} 必须为非负十进制浮点数。')

        if not allow_negative and value < 0:
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 {key} 必须为非负十进制浮点数。')

        return float(value)

    def _parse_headers(self, section_proxy: SectionProxy, key: str) -> tuple[tuple[str, str], ...]:
        """
        @brief 解析可选的 JSON 请求头配置。
        @details 缺失时返回空元组；存在时必须为键和值均为字符串的 JSON 对象，并保持声明顺序。
        @param section_proxy 包含目标键的配置节
        @param key 待读取的配置键
        @return 不可变的请求头键值对元组
        @throws ConfigError 当 JSON 格式、结构或键值类型不符合约束时
        """
        value: str | None = section_proxy.get(key)
        if value is None:
            return ()

        try:
            headers = loads(value)
        except JSONDecodeError as error:
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 header 必须为 JSON 对象。') from error

        if not isinstance(headers, dict):
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 header 必须为 JSON 对象。')

        if not all(isinstance(key, str) and isinstance(item, str) for key, item in headers.items()):
            raise ConfigError(f'配置文件 {self.path} 的 [{section_proxy.name}] 节键 header 的键和值必须为字符串。')

        return tuple(headers.items())


if __name__ == '__main__':
    pass
