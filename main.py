# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""同步 HTTP tracker 入口与应用生命周期。"""

from logging import getLogger
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from os import getenv

from assembler import Assembler
from config import Config
from file import File
from parser import PARSER_REGISTRY, ParserFactory

logger = getLogger(__name__)


class TrackerHandler(BaseHTTPRequestHandler):
    """
    @brief 提供 tracker 文件内容的 HTTP 读取接口。
    @details GET 返回 UTF-8 文本内容，HEAD 仅返回相同响应头；其他未实现方法按 HTTP 服务约定返回错误响应。
    """

    def __init__(self, *args, file: File, **kwargs):
        """
        @brief 初始化绑定文件对象的 HTTP 请求处理器。
        @param args BaseHTTPRequestHandler 的位置参数
        @param file 提供待发布文本内容的文件对象
        @param kwargs BaseHTTPRequestHandler 的其他关键字参数
        @return 无返回值；完成文件对象绑定并初始化父类处理器。
        """
        self._file: File = file
        super().__init__(*args, **kwargs)

    def _send_content(self, include_body: bool) -> None:
        """
        @brief 发送文件内容的成功响应。
        @details 响应体按 UTF-8 编码并设置文本类型与字节长度；include_body 为 False 时只发送响应头。
        @param include_body 是否写入响应体
        @return 无返回值；完成 HTTP 响应发送。
        """
        content: str = self._file.read()
        body: bytes = content.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()

        if include_body and body:
            self.wfile.write(body)

    def do_GET(self) -> None:
        """
        @brief 处理 GET 请求。
        @return 无返回值；发送健康状态或包含文件内容的成功响应。
        """
        if self.path == '/health':
            body: bytes = b'OK\n'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self._send_content(True)

    def do_HEAD(self) -> None:
        """
        @brief 处理 HEAD 请求。
        @return 无返回值；发送健康状态或不包含响应体的成功响应。
        """
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        self._send_content(False)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """
        @brief 发送 HTTP 错误响应。
        @details 未实现的方法代码 501 被转换为 405，并声明允许 GET 与 HEAD；其他状态码交由父类处理。
        @param code 原始 HTTP 状态码
        @param message 可选的错误消息
        @param explain 可选的错误说明
        @return 无返回值；完成错误响应发送。
        """
        if code == 501:
            self.send_response(405)
            self.send_header('Allow', 'GET, HEAD')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        super().send_error(code, message, explain)

    def log_message(self, format: str, *args: object) -> None:
        """
        @brief 记录 HTTP 请求处理日志。
        @param format 日志格式字符串
        @param args 格式化日志参数
        @return 无返回值；将请求日志写入项目日志记录器。
        """
        logger.info(format, *args)


if __name__ == '__main__':
    config_object: Config = Config(getenv('CONFIG_PATH', 'config.ini'))
    file_object: File = File(config_object.config.global_config.output_file)

    parser_factory: ParserFactory = ParserFactory(PARSER_REGISTRY)
    parser_factory.build_configured_parsers(config_object.config.parser_sections)

    assembler_object: Assembler = Assembler(config_object.config, file_object, parser_factory)

    handler: partial[TrackerHandler] = partial(TrackerHandler, file=file_object)
    server: HTTPServer = HTTPServer((config_object.config.global_config.host, config_object.config.global_config.port), handler)

    stop_event: Event = Event()

    worker: Thread = Thread(target=assembler_object.run, args=(stop_event,), daemon=False)
    worker.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()
        worker.join()
