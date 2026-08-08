# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证解析器注册、封装与公开数据契约。
@details 覆盖基础解析器的装饰器注册、配置化单参数封装、命名空间约束和异常传播。
"""

import inspect
from collections.abc import Mapping

import pytest

from config import RawParserSection
from parser import ParserError, ParserFactory, ParserRegistry, RawRequest


@pytest.fixture
def raw_request() -> RawRequest:
    """
    @brief 创建供解析器测试使用的成功响应视图。
    @return 固定的成功上游响应。
    """
    return RawRequest(
        body=b'udp://tracker.example:80\n',
        content_type='text/plain',
        final_url='https://example.invalid/final',
        original_url='https://example.invalid/original',
        status_code=200,
    )


@pytest.fixture
def registry() -> ParserRegistry:
    """
    @brief 创建彼此隔离的基础解析器注册表。
    @return 空的基础解析器注册表。
    """
    return ParserRegistry()


def test_raw_request_preserves_success_response_metadata(raw_request: RawRequest) -> None:
    """
    @brief 验证响应视图保留解析所需的安全元数据。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    assert raw_request.body == b'udp://tracker.example:80\n'
    assert raw_request.status_code == 200
    with pytest.raises(AttributeError):
        raw_request.status_code = 503  # type: ignore[misc]  # 验证冻结响应视图不可修改


def test_parser_error_is_domain_exception() -> None:
    """
    @brief 验证解析器领域异常可被调用方捕获。
    @return 无返回值。
    """
    with pytest.raises(ParserError):
        raise ParserError('无效响应内容')


def test_registry_registers_and_returns_base_parser(registry: ParserRegistry, raw_request: RawRequest) -> None:
    """
    @brief 验证装饰器注册基础解析器并保留原始调用契约。
    @param registry 独立的基础解析器注册表。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        assert request is raw_request
        assert options == {'prefix': 'udp'}
        return ['udp://tracker.example:80']

    assert registry.get('base-v1') is base_parser
    assert base_parser(raw_request, {'prefix': 'udp'}) == ['udp://tracker.example:80']


@pytest.mark.parametrize('name', ['', '   ', 1])
def test_registry_rejects_invalid_names(registry: ParserRegistry, name: object) -> None:
    """
    @brief 验证注册表拒绝空白或非字符串名称。
    @param registry 独立的基础解析器注册表。
    @param name 待注册的无效名称。
    @return 无返回值。
    """
    with pytest.raises(ParserError):
        registry.register(name)  # type: ignore[arg-type]  # 验证运行时名称类型校验


def test_registry_rejects_duplicate_name(registry: ParserRegistry) -> None:
    """
    @brief 验证注册表拒绝重复的基础解析器名称。
    @param registry 独立的基础解析器注册表。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def first_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        return []

    with pytest.raises(ParserError, match='base-v1'):
        registry.register('base-v1')


def test_registry_rejects_unknown_base_parser(registry: ParserRegistry) -> None:
    """
    @brief 验证注册表拒绝未注册的基础解析器名称。
    @param registry 独立的基础解析器注册表。
    @return 无返回值。
    """
    with pytest.raises(ParserError, match='missing-v1'):
        registry.get('missing-v1')


def test_factory_builds_parser_with_immutable_options(registry: ParserRegistry, raw_request: RawRequest) -> None:
    """
    @brief 验证工厂为配置别名绑定独立且不可变的选项快照。
    @param registry 独立的基础解析器注册表。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        assert request is raw_request
        with pytest.raises(TypeError):
            options['new'] = 'value'  # type: ignore[index]  # 验证工厂传入只读选项
        return [options['prefix']]

    factory = ParserFactory(registry)
    configured = factory.build_configured_parsers((
        RawParserSection('configured-v1', 'base-v1', (('prefix', 'udp'),)),
    ))

    assert configured['configured-v1'](raw_request) == ['udp']


def test_factory_rejects_configured_name_conflicting_with_base(registry: ParserRegistry) -> None:
    """
    @brief 验证配置别名不能占用基础解析器名称。
    @param registry 独立的基础解析器注册表。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        return []

    factory = ParserFactory(registry)
    sections = (RawParserSection('base-v1', 'base-v1', ()),)

    with pytest.raises(ParserError, match='base-v1'):
        factory.build_configured_parsers(sections)


def test_factory_rejects_duplicate_configured_names(registry: ParserRegistry) -> None:
    """
    @brief 验证工厂拒绝重复的配置解析器别名。
    @param registry 独立的基础解析器注册表。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        return []

    factory = ParserFactory(registry)
    sections = (
        RawParserSection('configured-v1', 'base-v1', ()),
        RawParserSection('configured-v1', 'base-v1', ()),
    )

    with pytest.raises(ParserError, match='configured-v1'):
        factory.build_configured_parsers(sections)


def test_factory_rejects_configured_parser_as_base(registry: ParserRegistry) -> None:
    """
    @brief 验证配置化解析器不能作为另一个配置化解析器的基础。
    @param registry 独立的基础解析器注册表。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        return []

    factory = ParserFactory(registry)
    sections = (
        RawParserSection('configured-v1', 'base-v1', ()),
        RawParserSection('nested-v1', 'configured-v1', ()),
    )

    with pytest.raises(ParserError, match='configured-v1'):
        factory.build_configured_parsers(sections)


def test_factory_resolves_direct_base_to_single_argument_parser(registry: ParserRegistry, raw_request: RawRequest) -> None:
    """
    @brief 验证直接基础引用也被封装为只接收请求对象的解析器。
    @param registry 独立的基础解析器注册表。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        assert request is raw_request
        assert options == {}
        with pytest.raises(TypeError):
            options['new'] = 'value'  # type: ignore[index]  # 验证工厂传入只读空选项
        return []

    factory = ParserFactory(registry)
    parser = factory.resolve_parser('base-v1', {})

    assert len(inspect.signature(parser).parameters) == 1
    assert parser(raw_request) == []


def test_factory_resolves_configured_parser_before_base(registry: ParserRegistry, raw_request: RawRequest) -> None:
    """
    @brief 验证工厂按名称返回已构造的配置解析器。
    @param registry 独立的基础解析器注册表。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        return [options['value']]

    factory = ParserFactory(registry)
    configured = factory.build_configured_parsers((
        RawParserSection('configured-v1', 'base-v1', (('value', 'configured'),)),
    ))

    assert factory.resolve_parser('configured-v1', configured)(raw_request) == ['configured']


def test_factory_propagates_parser_error(registry: ParserRegistry, raw_request: RawRequest) -> None:
    """
    @brief 验证基础解析器的领域异常不会被封装层吞掉或重包装。
    @param registry 独立的基础解析器注册表。
    @param raw_request 成功上游响应视图。
    @return 无返回值。
    """
    expected_error = ParserError('无效响应内容')

    @registry.register('base-v1')
    def base_parser(request: RawRequest, options: Mapping[str, str]) -> list[str]:
        raise expected_error

    factory = ParserFactory(registry)
    configured = factory.build_configured_parsers((
        RawParserSection('configured-v1', 'base-v1', ()),
    ))

    with pytest.raises(ParserError) as error_info:
        factory.resolve_parser('configured-v1', configured)(raw_request)

    assert error_info.value is expected_error


if __name__ == '__main__':
    pass
