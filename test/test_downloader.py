import unittest
from concurrent.futures import Future
from unittest.mock import patch
from urllib.request import Request

from tracker_collector.download import Downloader


class TestDownloader(unittest.TestCase):
    @patch('tracker_collector.download.ThreadPoolExecutor')
    def test_init(self, mock_executor):
        """
        Test the initialization method
        测试初始化方法
        """
        Downloader()
        mock_executor.assert_called_once_with(max_workers=8)

    @patch('tracker_collector.download.ThreadPoolExecutor')
    def test_get(self, mock_executor):
        """
        Test the get method
        测试get方法
        """
        mock_future = Future()
        mock_executor.return_value.submit.return_value = mock_future
        downloader = Downloader(workers=4)

        # 模拟一个Request对象
        # Mock a Request object
        mock_request = Request('http://example.com')
        mock_request.method = 'GET'

        # 调用get方法
        # Call the get method
        futures = downloader.get(mock_request)

        # 验证调用
        # Verify the call
        mock_executor.return_value.submit.assert_called_once_with(downloader._load_request, mock_request)
        self.assertEqual(len(futures), 1)
        self.assertIs(futures[0], mock_future)


if __name__ == '__main__':
    unittest.main()

