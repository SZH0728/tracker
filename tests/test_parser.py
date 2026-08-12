# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证解析器注册、封装与原生响应契约。
@details 覆盖基础解析器的装饰器注册、配置化单参数封装、命名空间约束和异常传播。
"""

import inspect
from collections.abc import Mapping

import pytest
from requests import PreparedRequest, Response

from config import RawParserSection
from parser import ParserError, ParserFactory, ParserRegistry


@pytest.fixture
def response() -> Response:
    """
    @brief 创建供解析器测试使用的原生成功响应。
    @return 填充完成的 requests.Response。
    """
    prepared_request = PreparedRequest()
    prepared_request.prepare(method='GET', url='https://example.invalid/original')
    native_response = Response()
    native_response._content = b'udp://tracker.example:80\n'
    native_response._content_consumed = True
    native_response.status_code = 200
    native_response.url = 'https://example.invalid/final'
    native_response.headers['Content-Type'] = 'text/plain'
    native_response.request = prepared_request
    return native_response


@pytest.fixture
def registry() -> ParserRegistry:
    """
    @brief 创建彼此隔离的基础解析器注册表。
    @return 空的基础解析器注册表。
    """
    return ParserRegistry()


def test_parser_receives_native_response_metadata(response: Response) -> None:
    assert response.content == b'udp://tracker.example:80\n'
    assert response.status_code == 200
    assert response.url == 'https://example.invalid/final'
    assert response.request.url == 'https://example.invalid/original'


def test_parser_error_is_domain_exception() -> None:
    with pytest.raises(ParserError):
        raise ParserError('无效响应内容')


def test_registry_registers_and_returns_base_parser(registry: ParserRegistry, response: Response) -> None:
    decorator = registry.register('base-v1')
    assert inspect.isfunction(decorator)

    @decorator
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        assert received_response is response
        assert options == {'prefix': 'udp'}
        return ['udp://tracker.example:80']

    assert registry.get('base-v1') is base_parser
    assert base_parser(response, {'prefix': 'udp'}) == ['udp://tracker.example:80']


@pytest.mark.parametrize('name', ['', '   ', 1])
def test_registry_rejects_invalid_names(registry: ParserRegistry, name: object) -> None:
    with pytest.raises(ParserError):
        registry.register(name)  # type: ignore[arg-type]  # 验证运行时名称类型校验


def test_registry_rejects_duplicate_name(registry: ParserRegistry) -> None:
    @registry.register('base-v1')
    def first_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return []

    with pytest.raises(ParserError, match='base-v1'):
        registry.register('base-v1')


def test_registry_rejects_unknown_base_parser(registry: ParserRegistry) -> None:
    with pytest.raises(ParserError, match='missing-v1'):
        registry.get('missing-v1')


def test_factory_builds_parser_with_immutable_options(registry: ParserRegistry, response: Response) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        assert received_response is response
        with pytest.raises(TypeError):
            options['new'] = 'value'  # type: ignore[index]  # 验证工厂传入只读选项
        return [options['prefix']]

    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('configured-v1', 'base-v1', (('prefix', 'udp'),)),))

    assert factory.resolve_parser('configured-v1')(response) == ['udp']


def test_factory_rejects_configured_name_conflicting_with_base(registry: ParserRegistry) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return []

    with pytest.raises(ParserError, match='base-v1'):
        ParserFactory(registry).build_configured_parsers((RawParserSection('base-v1', 'base-v1', ()),))


def test_factory_rejects_duplicate_configured_names(registry: ParserRegistry) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return []

    sections = (RawParserSection('configured-v1', 'base-v1', ()), RawParserSection('configured-v1', 'base-v1', ()))
    with pytest.raises(ParserError, match='configured-v1'):
        ParserFactory(registry).build_configured_parsers(sections)


def test_factory_rejects_configured_parser_as_base(registry: ParserRegistry) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return []

    sections = (RawParserSection('configured-v1', 'base-v1', ()), RawParserSection('nested-v1', 'configured-v1', ()))
    with pytest.raises(ParserError, match='configured-v1'):
        ParserFactory(registry).build_configured_parsers(sections)


def test_factory_resolves_direct_base_to_single_argument_parser(registry: ParserRegistry, response: Response) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        assert received_response is response
        assert options == {}
        with pytest.raises(TypeError):
            options['new'] = 'value'  # type: ignore[index]  # 验证工厂传入只读空选项
        return []

    factory = ParserFactory(registry)
    factory.build_configured_parsers(())
    parser = factory.resolve_parser('base-v1')

    assert inspect.isfunction(parser)
    assert parser is factory.resolve_parser('base-v1')
    assert len(inspect.signature(parser).parameters) == 1
    assert parser(response) == []


def test_factory_refreshes_base_parser_table_only_during_build(registry: ParserRegistry, response: Response) -> None:
    @registry.register('first-v1')
    def first_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return ['first']

    factory = ParserFactory(registry)
    factory.build_configured_parsers(())

    @registry.register('second-v1')
    def second_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return ['second']

    with pytest.raises(ParserError, match='second-v1'):
        factory.resolve_parser('second-v1')

    factory.build_configured_parsers(())
    assert factory.resolve_parser('first-v1')(response) == ['first']
    assert factory.resolve_parser('second-v1')(response) == ['second']


def test_factory_resolves_configured_parser_before_base(registry: ParserRegistry, response: Response) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return [options['value']]

    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('configured-v1', 'base-v1', (('value', 'configured'),)),))
    parser = factory.resolve_parser('configured-v1')

    assert inspect.isfunction(parser)
    assert len(inspect.signature(parser).parameters) == 1
    assert parser(response) == ['configured']


def test_factory_propagates_parser_error(registry: ParserRegistry, response: Response) -> None:
    expected_error = ParserError('无效响应内容')

    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        raise expected_error

    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('configured-v1', 'base-v1', ()),))

    with pytest.raises(ParserError) as error_info:
        factory.resolve_parser('configured-v1')(response)
    assert error_info.value is expected_error


def test_factory_replaces_configured_parser_table(registry: ParserRegistry, response: Response) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return [options['value']]

    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('first-v1', 'base-v1', (('value', 'first'),)),))
    factory.build_configured_parsers((RawParserSection('second-v1', 'base-v1', (('value', 'second'),)),))

    with pytest.raises(ParserError, match='first-v1'):
        factory.resolve_parser('first-v1')
    assert factory.resolve_parser('second-v1')(response) == ['second']


def test_factory_retains_previous_table_after_failed_build(registry: ParserRegistry, response: Response) -> None:
    @registry.register('base-v1')
    def base_parser(received_response: Response, options: Mapping[str, str]) -> list[str]:
        return [options['value']]

    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('configured-v1', 'base-v1', (('value', 'saved'),)),))

    with pytest.raises(ParserError, match='missing-v1'):
        factory.build_configured_parsers((RawParserSection('replacement-v1', 'missing-v1', ()),))
    assert factory.resolve_parser('configured-v1')(response) == ['saved']


if __name__ == '__main__':
    pass
