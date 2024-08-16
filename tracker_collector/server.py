# -*- coding:utf-8 -*-
# AUTHOR: Sun

from threading import Thread
from logging import getLogger
from http.server import BaseHTTPRequestHandler, HTTPServer

from config import Config

logger = getLogger(__name__)

CONFIG = Config()
# File path
# 文件路径
FILE_PATH = CONFIG.get('base', 'save_file')

# Whether to enable the server, port and the required request header
# 服务器是否启用、端口和必须的请求头
ENABLE = CONFIG.get('server', 'enable')
PORT = CONFIG.get('server', 'port')
REQUIRE_HEADERS = CONFIG.get('server', 'require_headers')


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Define HTTP request handler class
    定义HTTP请求处理器类
    """
    def do_GET(self):
        """
        Process GET requests
        处理GET请求
        """
        try:
            self.get_method()
        except Exception as e:
            # Record the error
            # 记录错误
            logger.error(e, exc_info=True)
            self.send_error(500)

    def get_method(self):
        """
        GET method logic
        GET方法的具体逻辑
        """
        # Verify that the request header meets the requirements
        # 验证请求头是否符合要求
        for key, value in REQUIRE_HEADERS.items():
            if key not in self.headers or self.headers[key] != value:
                self.send_error(403)
                return

        # Check whether the path is legal
        # 检查路径是否合法
        if self.path not in ('/', '/all', f'/{FILE_PATH}'):
            self.send_error(404)
            return

        # Send response header
        # 发送响应头
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        try:
            # Read the file and send the content
            # 读取文件并发送内容
            with open(FILE_PATH, 'rb') as f:
                contents = f.read()
            self.wfile.write(contents)
        except FileNotFoundError:
            self.send_error(404)
            logger.error(f'File {FILE_PATH} not found')

    def log_message(self, format_: str, *args) -> None:
        """
        Custom log recording method
        自定义日志记录方法
        """
        logger.info(format_ % args)


class Run(Thread):
    """
    Define the server thread class
    定义服务器线程类
    """
    def start(self):
        """
        Start the server according to the configuration
        根据配置启动服务器
        """
        if ENABLE:
            logger.info('Enabled server')
            super().start()
        else:
            logger.info('Disabled server')

    def run(self):
        """
        Run the server
        运行服务器
        """
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, HTTPRequestHandler)
        logger.info(f'Server running on port {PORT}')
        logger.warning('This server can only be used in intranet, please do not expose it to the Internet!')
        httpd.serve_forever()


if __name__ == '__main__':
    thread = Run()
    thread.start()
    thread.join()
