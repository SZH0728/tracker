# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""同步 HTTP tracker 入口与应用生命周期。"""

from logging import getLogger
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread

from assembler import Assembler
from config import Config
from file import File
from parser import PARSER_REGISTRY, ParserFactory

logger = getLogger(__name__)


class TrackerHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, file: File, **kwargs):
        self._file: File = file
        super().__init__(*args, **kwargs)

    def _send_content(self, include_body: bool) -> None:
        content: str = self._file.read()
        body: bytes = content.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()

        if include_body and body:
            self.wfile.write(body)

    def do_GET(self) -> None:
        self._send_content(True)

    def do_HEAD(self) -> None:
        self._send_content(False)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        if code == 501:
            self.send_response(405)
            self.send_header('Allow', 'GET, HEAD')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        super().send_error(code, message, explain)

    def log_message(self, format: str, *args: object) -> None:
        logger.info(format, *args)


if __name__ == '__main__':
    config_object: Config = Config('')
    file_object: File = File(config_object.config.global_config.output_file)

    parser_factory: ParserFactory = ParserFactory(PARSER_REGISTRY)
    parser_factory.build_configured_parsers(config_object.config.parser_sections)

    assembler_object: Assembler = Assembler(config_object.config, file_object, parser_factory)

    handler: partial[TrackerHandler] = partial(TrackerHandler, file=file_object)
    server: HTTPServer = HTTPServer(('127.0.0.1', config_object.config.global_config.port), handler)

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
