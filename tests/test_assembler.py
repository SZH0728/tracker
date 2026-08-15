# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证 tracker 装配刷新流水线。
@details 使用记录型请求器、文件边界与解析器注册表覆盖来源顺序、失败隔离、无序去重和周期等待。
"""

from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from requests import Response

import assembler as assembler_module
from assembler import Assembler
from config import RawConfig, RawGlobalConfig, RawParserSection, RawTrackerSource
from parser import ParserError, ParserFactory, ParserRegistry


class RecordingRequester(object):
    """
    @brief 记录数据源请求并返回预设响应。
    @details 测试装配器时避免真实网络请求，并保留调用顺序。
    """

    def __init__(self, responses: dict[str, Response | None]) -> None:
        self._responses = responses
        self.received_sources: list[RawTrackerSource] = []

    def fetch(self, source: RawTrackerSource) -> Response | None:
        self.received_sources.append(source)
        return self._responses[source.name]


class RecordingFile(object):
    """
    @brief 记录规范内容发布尝试。
    @details 使用命令式发布接口验证装配器的发布条件，不执行文件 I/O。
    """

    def __init__(self, content: str = '') -> None:
        self.content = content
        self.published_contents: list[str] = []

    def publish(self, content: str) -> None:
        self.published_contents.append(content)
        self.content = content


def create_source(name: str, parser: str = 'text') -> RawTrackerSource:
    return RawTrackerSource(name, f'https://{name}.example/list', (), 1, 0, 0, parser)


def create_response(content: bytes = b'payload') -> Response:
    response = Response()
    response._content = content
    response._content_consumed = True
    response.status_code = 200
    return response


def create_config(sources: tuple[RawTrackerSource, ...], refresh_interval: int = 1) -> RawConfig:
    return RawConfig(
        RawGlobalConfig(8080, str(Path('trackers.txt')), refresh_interval),
        sources,
        (RawParserSection('text', 'test-parser', ()),),
    )


def create_parser_factory(base_parser: Callable[[Response, Mapping[str, str]], list[str]]) -> ParserFactory:
    registry = ParserRegistry()
    registry.register('test-parser')(base_parser)
    factory = ParserFactory(registry)
    factory.build_configured_parsers((RawParserSection('text', 'test-parser', ()),))
    return factory


def create_assembler(
    monkeypatch: pytest.MonkeyPatch,
    requester: RecordingRequester,
    file: RecordingFile,
    sources: tuple[RawTrackerSource, ...],
    base_parser: Callable[[Response, Mapping[str, str]], list[str]],
    refresh_interval: int = 1,
) -> Assembler:
    monkeypatch.setattr(assembler_module, 'Requester', lambda: requester)
    return Assembler(create_config(sources, refresh_interval), file, create_parser_factory(base_parser))  # type: ignore[arg-type]  # 测试边界仅需记录发布内容


@pytest.mark.parametrize('refresh_interval', [0, -1])
def test_assembler_rejects_non_positive_refresh_interval(
    monkeypatch: pytest.MonkeyPatch,
    refresh_interval: int,
) -> None:
    with pytest.raises(ValueError, match='刷新间隔'):
        create_assembler(
            monkeypatch,
            RecordingRequester({}),
            RecordingFile(),
            (),
            lambda response, options: [],
            refresh_interval,
        )


def test_assembler_publishes_deduplicated_urls_without_trailing_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    first_source = create_source('first')
    second_source = create_source('second')
    first_response = create_response(b'first')
    second_response = create_response(b'second')
    received_responses: list[Response] = []

    def parser(response: Response, options: Mapping[str, str]) -> list[str]:
        received_responses.append(response)
        if response is first_response:
            return ['udp://first.example', 'http://shared.example', 'udp://first.example']
        return ['http://shared.example', 'https://second.example']

    requester = RecordingRequester({'first': first_response, 'second': second_response})
    file = RecordingFile()
    assembler = create_assembler(monkeypatch, requester, file, (first_source, second_source), parser)

    assembler.refresh_once()

    assert requester.received_sources == [first_source, second_source]
    assert received_responses == [first_response, second_response]
    published_content = file.published_contents[0]
    assert not published_content.endswith('\n')
    assert set(published_content.split('\n')) == {
        'udp://first.example',
        'http://shared.example',
        'https://second.example',
    }


def test_assembler_skips_parser_when_requester_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    failed_source = create_source('failed')
    successful_source = create_source('successful')
    parser_was_called = False

    def parser(response: Response, options: Mapping[str, str]) -> list[str]:
        nonlocal parser_was_called
        parser_was_called = True
        return ['udp://successful.example']

    requester = RecordingRequester({'failed': None, 'successful': create_response()})
    file = RecordingFile()
    assembler = create_assembler(monkeypatch, requester, file, (failed_source, successful_source), parser)

    assembler.refresh_once()

    assert parser_was_called
    assert file.published_contents == ['udp://successful.example']


def test_assembler_isolates_parser_error_and_publishes_current_successes(monkeypatch: pytest.MonkeyPatch) -> None:
    failed_source = create_source('failed')
    successful_source = create_source('successful')

    def parser(response: Response, options: Mapping[str, str]) -> list[str]:
        if response.content == b'failed':
            raise ParserError('invalid payload')
        return ['udp://successful.example']

    requester = RecordingRequester({'failed': create_response(b'failed'), 'successful': create_response()})
    file = RecordingFile('udp://previous.example\n')
    assembler = create_assembler(monkeypatch, requester, file, (failed_source, successful_source), parser)

    assembler.refresh_once()

    assert file.published_contents == ['udp://successful.example']
    assert file.content == 'udp://successful.example'


def test_assembler_preserves_file_when_all_sources_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    first_source = create_source('first')
    second_source = create_source('second')

    def parser(response: Response, options: Mapping[str, str]) -> list[str]:
        raise ParserError('invalid payload')

    previous_content = 'udp://previous.example\n'
    file = RecordingFile(previous_content)
    assembler = create_assembler(
        monkeypatch,
        RecordingRequester({'first': None, 'second': create_response()}),
        file,
        (first_source, second_source),
        parser,
    )

    assembler.refresh_once()

    assert file.published_contents == []
    assert file.content == previous_content


def test_assembler_publishes_empty_content_when_a_source_succeeds_without_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    source = create_source('empty')
    file = RecordingFile('udp://previous.example\n')
    assembler = create_assembler(
        monkeypatch,
        RecordingRequester({'empty': create_response()}),
        file,
        (source,),
        lambda response, options: [],
    )

    assembler.refresh_once()

    assert file.published_contents == ['']
    assert file.content == ''


def test_assembler_isolates_unknown_parser_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    source = create_source('unknown', 'missing')
    file = RecordingFile('udp://previous.example\n')
    assembler = create_assembler(
        monkeypatch,
        RecordingRequester({'unknown': create_response()}),
        file,
        (source,),
        lambda response, options: [],
    )

    assembler.refresh_once()

    assert file.published_contents == []
    assert file.content == 'udp://previous.example\n'


def test_assembler_refreshes_before_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    source = create_source('first')
    file = RecordingFile()
    assembler = create_assembler(
        monkeypatch,
        RecordingRequester({'first': create_response()}),
        file,
        (source,),
        lambda response, options: ['udp://first.example'],
        3,
    )
    intervals: list[int] = []

    def stop_after_wait(interval: int) -> None:
        intervals.append(interval)
        raise RuntimeError('stop test loop')

    monkeypatch.setattr(assembler_module, 'sleep', stop_after_wait)

    with pytest.raises(RuntimeError, match='stop test loop'):
        assembler.run()

    assert file.published_contents == ['udp://first.example']
    assert intervals == [3]
def test_assembler_continues_after_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    assembler = create_assembler(
        monkeypatch,
        RecordingRequester({}),
        RecordingFile(),
        (),
        lambda response, options: [],
    )
    refresh_calls = 0

    def refresh_once() -> None:
        nonlocal refresh_calls
        refresh_calls += 1
        if refresh_calls == 1:
            raise KeyboardInterrupt
        raise RuntimeError('stop after interrupt')

    monkeypatch.setattr(assembler, 'refresh_once', refresh_once)
    monkeypatch.setattr(assembler_module, 'sleep', lambda interval: None)

    with pytest.raises(RuntimeError, match='stop after interrupt'):
        assembler.run()

    assert refresh_calls == 2


