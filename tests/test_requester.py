# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证上游请求的原生 requests 响应行为。
@details 使用本地 HTTPServer 演练请求头、source 级超时与重试、默认重定向和传输资源释放。
"""

from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import sleep

from requests import Response

from config import RawTrackerSource
from requester import Requester


class FixtureHandler(BaseHTTPRequestHandler):
    attempts: dict[str, int] = {}
    received_authorization: str | None = None

    def do_GET(self) -> None:
        FixtureHandler.attempts[self.path] = FixtureHandler.attempts.get(self.path, 0) + 1
        FixtureHandler.received_authorization = self.headers.get('Authorization')

        if self.path == '/success':
            self._send(200, b'payload', 'Text/Plain; charset=utf-8')
        elif self.path == '/header':
            self._send(200, b'header')
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/success')
            self.end_headers()
        elif self.path == '/timeout':
            sleep(1.2)
            self._send(200, b'late')
        elif self.path.startswith('/status/'):
            self._send(int(self.path.rsplit('/', maxsplit=1)[-1]), b'failure')
        elif self.path == '/retry-success':
            self._send(503 if FixtureHandler.attempts[self.path] < 3 else 200, b'ok')
        else:
            self._send(404, b'not-found')

    def _send(self, status_code: int, body: bytes, content_type: str = 'text/plain') -> None:
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except ConnectionAbortedError:
            pass

    def log_message(self, format: str, *args: object) -> None:
        pass


@contextmanager
def run_server() -> Iterator[str]:
    FixtureHandler.attempts = {}
    FixtureHandler.received_authorization = None
    server = HTTPServer(('127.0.0.1', 0), FixtureHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        host = str(server.server_address[0])
        port = int(server.server_address[1])
        yield f'http://{host}:{port}'
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def create_source(
    url: str,
    *,
    request_timeout: int = 1,
    retry: int = 0,
    retry_interval: int = 0,
    headers: tuple[tuple[str, str], ...] = (),
) -> RawTrackerSource:
    return RawTrackerSource(
        name='fixture',
        url=url,
        headers=headers,
        request_timeout=request_timeout,
        retry=retry,
        retry_interval=retry_interval,
        parser='text-lines-v1',
    )


def test_requester_returns_native_response_with_content_and_headers() -> None:
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/header', headers=(('Authorization', 'Bearer secret-token'),)))

    assert isinstance(response, Response)
    assert response.content == b'header'
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain'
    assert response.url == f'{base_url}/header'
    assert response.request.url == f'{base_url}/header'
    assert FixtureHandler.received_authorization == 'Bearer secret-token'


def test_requester_keeps_response_content_available_after_closing_transport() -> None:
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/success'))

    assert response is not None
    assert response.content == b'payload'
    assert response.raw.closed


def test_requester_retries_selected_server_failures_until_success(monkeypatch: object) -> None:
    delays: list[int] = []
    monkeypatch.setattr('requester.sleep', delays.append)  # type: ignore[attr-defined]  # 替换等待以验证重试间隔
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/retry-success', retry=3, retry_interval=2))

    assert response is not None
    assert response.content == b'ok'
    assert FixtureHandler.attempts['/retry-success'] == 3
    assert delays == [2, 2]


def test_requester_does_not_retry_client_errors(monkeypatch: object) -> None:
    delays: list[int] = []
    monkeypatch.setattr('requester.sleep', delays.append)  # type: ignore[attr-defined]  # 替换等待以验证未发生重试
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/status/404', retry=2, retry_interval=2))

    assert response is None
    assert FixtureHandler.attempts['/status/404'] == 1
    assert delays == []


def test_requester_retries_server_failures_without_waiting_after_last_attempt(monkeypatch: object) -> None:
    delays: list[int] = []
    monkeypatch.setattr('requester.sleep', delays.append)  # type: ignore[attr-defined]  # 替换等待以验证最后一次失败后不等待
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/status/503', retry=2, retry_interval=2))

    assert response is None
    assert FixtureHandler.attempts['/status/503'] == 3
    assert delays == [2, 2]


def test_requester_uses_requests_default_redirects() -> None:
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/redirect'))

    assert response is not None
    assert response.content == b'payload'
    assert response.url == f'{base_url}/success'
    assert len(response.history) == 1
    assert response.history[0].status_code == 302


def test_requester_retries_timeouts_without_exceeding_limit(monkeypatch: object) -> None:
    delays: list[int] = []
    monkeypatch.setattr('requester.sleep', delays.append)  # type: ignore[attr-defined]  # 替换等待以验证 source 级重试间隔
    with run_server() as base_url:
        with Requester() as requester:
            response = requester.fetch(create_source(f'{base_url}/timeout', request_timeout=1, retry=1, retry_interval=2))

    assert response is None
    assert delays == [2]


def test_requester_retries_connection_failures(monkeypatch: object) -> None:
    delays: list[int] = []
    monkeypatch.setattr('requester.sleep', delays.append)  # type: ignore[attr-defined]  # 替换等待以验证连接失败重试
    with Requester() as requester:
        response = requester.fetch(create_source('http://127.0.0.1:1/no-server', request_timeout=1, retry=2, retry_interval=2))

    assert response is None
    assert delays == [2, 2]


if __name__ == '__main__':
    pass
