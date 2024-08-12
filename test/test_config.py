# -*- coding:utf-8 -*-
# AUTHOR: Sun

import unittest

from tracker_collector.config import Config

data = """
[base]
thread_pool_size = 5
save_file = /path/to/save/file.txt
tracker = example, another

[request]
default_headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
timeout = 10

[interval]
second = 1
minute = 60
hour = 3600
day = 86400

[logger]
log_file = /path/to/log/file.log
log_level = INFO

[tracker_example]
url = http://example.com/tracker
method = 
headers = {"X-API-Key": "12345"}

[tracker_another]
url = http://another-example.com/tracker
method = SPLIT()
headers = {"Authorization": "Bearer token12345"}
"""


class TestConfig(unittest.TestCase):
    def test_config_with_dictionary_like_interface(self):
        """
        Test Config class with dictionary-like interface.
        使用类字典接口测试 Config 类的功能。
        """
        config = Config(data)

        # Test the base section
        # 测试 base 部分
        self.assertEqual(5, config['base.thread_pool_size'])
        self.assertEqual('/path/to/save/file.txt', config['base.save_file'])
        self.assertEqual(['example', 'another'], config['base.tracker'])

        # Test the request section
        # 测试 request 部分
        self.assertEqual({'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}, config['request.default_headers'])
        self.assertEqual(10, config['request.timeout'])

        # Test the interval section
        # 测试 interval 部分
        self.assertEqual(1, config['interval.second'])
        self.assertEqual(60, config['interval.minute'])
        self.assertEqual(3600, config['interval.hour'])
        self.assertEqual(86400, config['interval.day'])

        # Test the logger section
        # 测试 logger 部分
        self.assertEqual('/path/to/log/file.log', config['logger.log_file'])
        self.assertEqual('INFO', config['logger.log_level'])

        # Test the tracker_* section
        # 测试 tracker_* 部分
        self.assertEqual('http://example.com/tracker', config['tracker_example.url'])
        self.assertEqual('', config['tracker_example.method'])
        self.assertEqual({'X-API-Key': '12345'}, config['tracker_example.headers'])

        self.assertEqual('http://another-example.com/tracker', config['tracker_another.url'])
        self.assertEqual('SPLIT()', config['tracker_another.method'])
        self.assertEqual({'Authorization': 'Bearer token12345'}, config['tracker_another.headers'])

    def test_config_with_two_dimensional_dictionary_like_interface(self):
        """
        Test Config class with two-dimensional dictionary-like interface.
        使用类两维字典接口测试 Config 类的功能。
        """
        config = Config(data)

        # Test the base section
        # 测试 base 部分
        self.assertEqual(5, config['base']['thread_pool_size'])
        self.assertEqual('/path/to/save/file.txt', config['base']['save_file'])
        self.assertEqual(['example', 'another'], config['base']['tracker'])

        # Test the request section
        # 测试 request 部分
        self.assertEqual({'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}, config['request']['default_headers'])
        self.assertEqual(10, config['request']['timeout'])

        # Test the interval section
        # 测试 interval 部分
        self.assertEqual(1, config['interval']['second'])
        self.assertEqual(60, config['interval']['minute'])
        self.assertEqual(3600, config['interval']['hour'])
        self.assertEqual(86400, config['interval']['day'])

        # Test the logger section
        # 测试 logger 部分
        self.assertEqual('/path/to/log/file.log', config['logger']['log_file'])
        self.assertEqual('INFO', config['logger']['log_level'])

        # Test the tracker_* section
        # 测试 tracker_* 部分
        self.assertEqual('http://example.com/tracker', config['tracker_example']['url'])
        self.assertEqual('', config['tracker_example']['method'])
        self.assertEqual({'X-API-Key': '12345'}, config['tracker_example']['headers'])

        self.assertEqual('http://another-example.com/tracker', config['tracker_another']['url'])
        self.assertEqual('SPLIT()', config['tracker_another']['method'])
        self.assertEqual({'Authorization': 'Bearer token12345'}, config['tracker_another']['headers'])

    def test_config_with_get_interface(self):
        """
        Test Config class with get interface.
        使用 get 接口测试 Config 类的功能。
        """
        config = Config(data)

        # Test the base section
        # 测试 base 部分
        self.assertEqual(5, config.get('base', 'thread_pool_size'))
        self.assertEqual('/path/to/save/file.txt', config.get('base', 'save_file'))
        self.assertEqual(['example', 'another'], config.get('base', 'tracker'))

        # Test the request section
        # 测试 request 部分
        self.assertEqual({'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}, config.get('request', 'default_headers'))
        self.assertEqual(10, config.get('request', 'timeout'))

        # Test the interval section
        # 测试 interval 部分
        self.assertEqual(1, config.get('interval', 'second'))
        self.assertEqual(60, config.get('interval', 'minute'))
        self.assertEqual(3600, config.get('interval', 'hour'))
        self.assertEqual(86400, config.get('interval', 'day'))

        # Test the logger section
        # 测试 logger 部分
        self.assertEqual('/path/to/log/file.log', config.get('logger', 'log_file'))
        self.assertEqual('INFO', config.get('logger', 'log_level'))

        # Test the tracker_* section
        # 测试 tracker_* 部分
        self.assertEqual('http://example.com/tracker', config.get('tracker_example', 'url'))
        self.assertEqual('', config.get('tracker_example', 'method'))
        self.assertEqual({'X-API-Key': '12345'}, config.get('tracker_example', 'headers'))

        self.assertEqual('http://another-example.com/tracker', config.get('tracker_another', 'url'))
        self.assertEqual('SPLIT()', config.get('tracker_another', 'method'))
        self.assertEqual({'Authorization': 'Bearer token12345'}, config.get('tracker_another', 'headers'))

    def test_config_with_attribute_like_interface(self):
        """
        Test Config class with attribute-like interface.
        使用类属性接口测试 Config 类的功能。
        """
        config = Config(data)

        # Test the base section
        # 测试 base 部分
        self.assertEqual(5, config.base.thread_pool_size)
        self.assertEqual('/path/to/save/file.txt', config.base.save_file)
        self.assertEqual(['example', 'another'], config.base.tracker)

        # Test the request section
        # 测试 request 部分
        self.assertEqual({'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}, config.request.default_headers)
        self.assertEqual(10, config.request.timeout)

        # Test the interval section
        # 测试 interval 部分
        self.assertEqual(1, config.interval.second)
        self.assertEqual(60, config.interval.minute)
        self.assertEqual(3600, config.interval.hour)
        self.assertEqual(86400, config.interval.day)

        # Test the logger section
        # 测试 logger 部分
        self.assertEqual('/path/to/log/file.log', config.logger.log_file)
        self.assertEqual('INFO', config.logger.log_level)

        # Test the tracker_* section
        # 测试 tracker_* 部分
        self.assertEqual('http://example.com/tracker', config.tracker_example.url)
        self.assertEqual('', config.tracker_example.method)
        self.assertEqual({'X-API-Key': '12345'}, config.tracker_example.headers)

        self.assertEqual('http://another-example.com/tracker', config.tracker_another.url)
        self.assertEqual('SPLIT()', config.tracker_another.method)
        self.assertEqual({'Authorization': 'Bearer token12345'}, config.tracker_another.headers)


if __name__ == '__main__':
    unittest.main()
