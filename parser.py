# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义解析器边界的响应视图与调用类型。
@details 后续解析器注册表只接收成功获取后的响应视图，不读取配置文件、不执行网络或文件操作。
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from config import RawParserSection


class ParserError(Exception):
    """
    @brief 表示响应内容、解析器选项或候选 URL 无效。
    @details 有效但不含 tracker URL 的响应应由未来解析器返回空列表，而不是抛出此异常。
    """


@dataclass(frozen=True, slots=True)
class RawRequest(object):
    """
    @brief 表示传递给解析器的成功上游响应。
    @details 此记录仅包含解析器策略需要的响应正文与安全元数据。
    """

    body: bytes  # 上游响应正文的原始字节
    content_type: str | None  # 已规范化的响应内容类型
    final_url: str  # 成功响应的最终地址
    original_url: str  # 配置的初始请求地址
    status_code: int  # 成功响应的 HTTP 状态码


BaseParser = Callable[[RawRequest, Mapping[str, str]], list[str]]
ConfiguredParser = Callable[[RawRequest], list[str]]

_EMPTY_OPTIONS: Mapping[str, str] = MappingProxyType({})


class _ConfiguredParser(object):
    """封装基础解析器及其不可变选项。"""

    def __init__(self, base_parser: BaseParser, options: Mapping[str, str]) -> None:
        self._base_parser = base_parser
        self._options = options

    def __call__(self, raw_request: RawRequest) -> list[str]:
        return self._base_parser(raw_request, self._options)


class _ParserRegistrar(object):
    """将基础解析器注册到指定注册表。"""

    def __init__(self, registry: 'ParserRegistry', name: str) -> None:
        self._registry = registry
        self._name = name

    def __call__(self, base_parser: BaseParser) -> BaseParser:
        self._registry._register(self._name, base_parser)
        return base_parser


class ParserRegistry(object):
    """
    @brief 管理基础解析器的注册与按名称查找。
    @details 注册表只保存双参数基础解析器，不保存配置化解析器或配置数据。
    """

    def __init__(self) -> None:
        """
        @brief 初始化空的基础解析器注册表。
        @return 无返回值；创建空注册表。
        """
        self._parsers: dict[str, BaseParser] = {}

    def register(self, name: str) -> Callable[[BaseParser], BaseParser]:
        """
        @brief 创建基础解析器注册装饰器。
        @param name 基础解析器的唯一名称。
        @return 接收并原样返回基础解析器的注册装饰器。
        @throws ParserError 当名称无效或已注册时。
        """
        self._raise_for_invalid_name(name)

        if self.contains(name):
            raise ParserError(f'基础解析器名称已注册：{name}')

        return _ParserRegistrar(self, name)

    def get(self, name: str) -> BaseParser:
        """
        @brief 获取指定名称的基础解析器。
        @param name 已注册基础解析器的名称。
        @return 保持双参数接口的基础解析器。
        @throws ParserError 当名称无效或未注册时。
        """
        self._raise_for_invalid_name(name)

        if name not in self._parsers:
            raise ParserError(f'未找到基础解析器：{name}')

        return self._parsers[name]

    def contains(self, name: str) -> bool:
        """
        @brief 判断指定名称是否已注册为基础解析器。
        @param name 待检查的基础解析器名称。
        @return 名称已注册时返回 True，否则返回 False。
        """
        return name in self._parsers

    def _register(self, name: str, base_parser: BaseParser) -> None:
        self._raise_for_invalid_name(name)
        if self.contains(name):
            raise ParserError(f'基础解析器名称已注册：{name}')
        self._parsers[name] = base_parser

    @staticmethod
    def _raise_for_invalid_name(name: str) -> None:
        if not isinstance(name, str):
            raise ParserError(f'基础解析器名称必须为字符串，实际类型为：{type(name).__name__}')

        if not name.strip():
            raise ParserError('基础解析器名称不能为空。')


class ParserFactory(object):
    """
    @brief 基于注册表构造供调用方使用的单参数解析器。
    @details 工厂解析配置别名或基础名称，并将基础解析器和不可变选项封装为统一调用接口。
    """

    def __init__(self, registry: ParserRegistry) -> None:
        """
        @brief 使用基础解析器注册表初始化工厂。
        @param registry 提供基础解析器的注册表。
        @return 无返回值；保存注入的注册表。
        """
        self._registry = registry

    def build_configured_parsers(self, parser_sections: Iterable[RawParserSection]) -> dict[str, ConfiguredParser]:
        """
        @brief 根据原始配置节构造配置化解析器。
        @details 每个配置别名捕获自己的基础解析器和不可变非 base 选项。
        @param parser_sections 来自配置边界的原始解析器配置节。
        @return 配置别名到单参数解析器的映射。
        @throws ParserError 当别名冲突、重复或基础解析器不存在时。
        """
        configured_parsers: dict[str, ConfiguredParser] = {}
        for section in parser_sections:
            self._raise_for_configured_name(section.name, configured_parsers)
            base_parser = self._registry.get(section.base)
            options: Mapping[str, str] = MappingProxyType(dict(section.options))
            configured_parsers[section.name] = _ConfiguredParser(base_parser, options)
        return configured_parsers

    def resolve_parser(self, reference: str, configured_parsers: Mapping[str, ConfiguredParser]) -> ConfiguredParser:
        """
        @brief 按配置别名或基础名称解析单参数解析器。
        @details 配置别名优先；直接基础名称会使用不可变空选项完成封装。
        @param reference 配置别名或基础解析器名称。
        @param configured_parsers 已构造的配置别名映射。
        @return 仅接收 RawRequest 的封装解析器。
        @throws ParserError 当引用无效或无法解析时。
        """
        if reference in configured_parsers:
            return configured_parsers[reference]
        return _ConfiguredParser(self._registry.get(reference), _EMPTY_OPTIONS)

    def _raise_for_configured_name(self, name: str, configured_parsers: Mapping[str, ConfiguredParser]) -> None:
        if not isinstance(name, str):
            raise ParserError(f'配置解析器别名必须为字符串，实际类型为：{type(name).__name__}')
        if not name.strip():
            raise ParserError('配置解析器别名不能为空。')
        if self._registry.contains(name):
            raise ParserError(f'配置解析器别名与基础解析器名称冲突：{name}')
        if name in configured_parsers:
            raise ParserError(f'配置解析器别名重复：{name}')


if __name__ == '__main__':
    pass
