import unittest
from unittest.mock import patch
from re import compile

from tracker_collector.analysis import Analysis, Split, Regex


class TestSplit(unittest.TestCase):

    @patch('tracker_collector.analysis.logger')
    def test_init_without_keyword(self, mock_logger):
        """
        Test the __init__ method when no keyword is provided.
        测试不提供关键词的情况。
        """
        split = Split()
        self.assertIsNone(split.keyword)
        self.assertIn('Split object initialized with keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_init_with_nonexistent_keyword(self, mock_logger):
        """
        Test the __init__ method when the keyword does not exist.
        测试未找到关键词的情况。
        """
        split = Split('SPLIT()')
        self.assertIsNone(split.keyword)
        self.assertIn('Split object initialized with keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_init_with_invalid_keyword(self, mock_logger):
        """
        Test the __init__ method when the keyword is invalid.
        测试关键词无效的情况。
        """
        split = Split('invalid(keyword)')
        self.assertIsNone(split.keyword)
        self.assertIn('is not a valid SPLIT method, use default method: SPLIT()', mock_logger.warning.call_args.args[0])
        self.assertIn('Split object initialized with keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_init_with_valid_keyword(self, mock_logger):
        """
        Test the __init__ method when the keyword is valid.
        测试关键词有效的情况。
        """
        split = Split('SPLIT(keyword)')
        self.assertEqual('keyword', split.keyword)
        self.assertIn('Split object initialized with keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_analyze_with_none_as_keyword(self, mock_logger):
        """
        Test the `analyze` method when the keyword is None.
        测试关键词为None的情况。
        """
        split = Split()

        result = split.analyze('data_one\ndata_two\ndata_three')
        self.assertEqual(['data_one', 'data_two', 'data_three'], result)
        self.assertIn('Splitting data using keyword:', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_analyze_with_valid_keyword(self, mock_logger):
        """
        Test the `analyze` method when the keyword is valid.
        测试关键词有效的情况。
        """
        split = Split('SPLIT(keyword)')
        result = split.analyze('data_one keyword data_two keyword data_three')
        self.assertEqual(['data_one', 'data_two', 'data_three'], result)
        self.assertIn('Splitting data using keyword:', mock_logger.debug.call_args.args[0])


class TestRegex(unittest.TestCase):

    @patch('tracker_collector.analysis.logger')
    def test_init_with_valid_regex(self, mock_logger):
        """
        Test the __init__ method when the keyword is a valid regex.
        测试当关键字是一个有效的正则表达式时的初始化方法。
        """
        regex = Regex('REGEX(keyword)')
        self.assertEqual('keyword', regex.keyword)
        self.assertEqual(compile('keyword'), regex.regex)
        self.assertIn('Regex object initialized with keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_init_with_invalid_regex(self, mock_logger):
        """
        Test the __init__ method when the keyword is an invalid regex.
        测试当关键字是一个无效的正则表达式时的初始化方法。
        """
        with self.assertRaises(ValueError):
            Regex('invalid(keyword))')

        self.assertIn('is not a valid REGEX method', mock_logger.warning.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_analyze_with_valid_regex(self, mock_logger):
        """
        Test the `analyze` method when the keyword is a valid regex.
        测试当关键字是一个有效的正则表达式时的 `analyze` 方法。
        """
        regex = Regex('REGEX((.*?) keyword)')
        result = regex.analyze('data_one keyword data_two keyword')
        self.assertEqual(result, ['data_one', 'data_two'])
        self.assertIn('Regex data using keyword', mock_logger.debug.call_args.args[0])

    @patch('tracker_collector.analysis.logger')
    def test_analyze_with_invalid_data(self, mock_logger):
        """
        Test the `analyze` method when the data does not match the regex.
        测试当数据与正则表达式不匹配时的 `analyze` 方法。
        """
        regex = Regex('REGEX(keyword)')
        result = regex.analyze('no kw here')
        self.assertEqual([], result)
        self.assertIn('Regex data using keyword', mock_logger.debug.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
