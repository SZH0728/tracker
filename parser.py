# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义解析器边界与调用类型。
@details 后续解析器注册表只接收成功获取后的原生 requests.Response，不读取配置文件、不执行网络或文件操作。
"""

from collections.abc import Callable, Iterable, Mapping
from types import MappingProxyType

from requests import Response

from config import RawParserSection


class ParserError(Exception):
    """
    @brief 表示响应内容、解析器选项或候选 URL 无效。
    @details 有效但不含 tracker URL 的响应应由未来解析器返回空列表，而不是抛出此异常。
    """


BaseParser = Callable[[Response, Mapping[str, str]], list[str]]
ConfiguredParser = Callable[[Response], list[str]]

EMPTY_OPTIONS: Mapping[str, str] = MappingProxyType({})


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

        def decorator(base_parser: BaseParser) -> BaseParser:
            self._parsers[name] = base_parser
            return base_parser

        return decorator

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

    def items(self) -> Mapping[str, BaseParser]:
        """
        @brief 获取基础解析器的只读快照。
        @return 基础解析器名称到双参数解析器的不可变映射。
        """
        return MappingProxyType(self._parsers)

    def contains(self, name: str) -> bool:
        """
        @brief 判断指定名称是否已注册为基础解析器。
        @param name 待检查的基础解析器名称。
        @return 名称已注册时返回 True，否则返回 False。
        """
        return name in self._parsers

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
        self._base_parsers: Mapping[str, ConfiguredParser] = MappingProxyType({})
        self._configured_parsers: Mapping[str, ConfiguredParser] = MappingProxyType({})

    def build_configured_parsers(self, parser_sections: Iterable[RawParserSection]) -> None:
        """
        @brief 根据原始配置节构造并安装配置化解析器。
        @details 先封装全部基础解析器，再构建配置别名；仅在全部构造成功后替换内部表。
        @param parser_sections 来自配置边界的原始解析器配置节。
        @throws ParserError 当别名冲突、重复或基础解析器不存在时。
        """
        base_parsers = self._registry.items()
        configured_base_parsers = {
            name: self._configure_parser(base_parser, EMPTY_OPTIONS)
            for name, base_parser in base_parsers.items()
        }
        configured_parsers: dict[str, ConfiguredParser] = {}

        for section in parser_sections:
            self._raise_for_configured_name(section.name, configured_parsers)

            base_parser = self._registry.get(section.base)
            options: Mapping[str, str] = MappingProxyType(dict(section.options))
            configured_parsers[section.name] = self._configure_parser(base_parser, options)

        self._base_parsers = MappingProxyType(configured_base_parsers)
        self._configured_parsers = MappingProxyType(configured_parsers)

    def resolve_parser(self, reference: str) -> ConfiguredParser:
        """
        @brief 按配置别名或基础名称解析单参数解析器。
        @details 配置别名优先；基础解析器必须已在最近一次构造中完成封装。
        @param reference 配置别名或基础解析器名称。
        @return 仅接收原生 Response 的封装解析器。
        @throws ParserError 当引用无效或无法解析时。
        """
        self._raise_for_configured_name(reference, None)

        if reference in self._configured_parsers:
            return self._configured_parsers[reference]

        if reference in self._base_parsers:
            return self._base_parsers[reference]

        raise ParserError(f'未找到基础解析器：{reference}')

    @staticmethod
    def _configure_parser(base_parser: BaseParser, options: Mapping[str, str]) -> ConfiguredParser:
        def configured_parser(response: Response) -> list[str]:
            return base_parser(response, options)

        return configured_parser

    def _raise_for_configured_name(self, name: str, configured_parsers: Mapping[str, ConfiguredParser] | None) -> None:
        if not isinstance(name, str):
            raise ParserError(f'配置解析器别名必须为字符串，实际类型为：{type(name).__name__}')

        if not name.strip():
            raise ParserError('配置解析器别名不能为空。')

        if configured_parsers is not None:
            if self._registry.contains(name):
                raise ParserError(f'配置解析器别名与基础解析器名称冲突：{name}')

            if name in configured_parsers:
                raise ParserError(f'配置解析器别名重复：{name}')


if __name__ == '__main__':
    pass
