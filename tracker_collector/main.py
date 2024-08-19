# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import getLogger
from time import sleep

from log import LogConfig, read_config
from config import Config
from download import Downloader
from analysis import Analysis
from server import Run

logger = getLogger(__name__)

PluginToLib = {
    'xpath': 'lxml',
    'css': 'PyQuery',
}


class Main(object):
    """
    Main class that handles the core functionality of the application.
    主类，负责应用程序的核心功能。
    """
    def __init__(self):
        self.config = Config()
        self.log_config = LogConfig(*read_config())
        self.downloader = self.create_downloader()
        self.analysis = self.create_analysis()

        plugin = self.config.get('base', 'plugin')
        for i in plugin:
            if i not in PluginToLib:
                logger.warning(f'Plugin {i} cannot be found, please make sure the spelling is correct')
                continue

            try:
                __import__(PluginToLib[i])
            except ImportError:
                logger.warning(f'Plugin {i} not found, please install it first')
                raise ImportError(f'Plugin {i} not found, please install it first')

        thread = Run()
        thread.start()

    def run(self):
        """
        Runs the main process of fetching data, analyzing it, and saving the results.
        运行主流程，包括获取数据、分析数据以及保存结果。
        """
        logger.info('Starting fetching data...')

        # Store unique trackers.
        # 存储唯一追踪器。
        trackers: set[str] = set()

        # Fetch URLs and headers from the configuration.
        # 获取URL和头部信息。
        for url, headers in self.gather_url():
            self.downloader.get(url, headers=headers)

        # Process completed requests.
        # 处理已完成的请求。
        for result, request in self.downloader.complete():
            if isinstance(result, Exception):
                # Skip any failed requests.
                # 跳过任何失败的请求。
                continue

            # Analyze the response and update the trackers set.
            # 分析响应，并更新追踪器集合。
            trackers.update(self.analysis.analyze(request.full_url, result))

        # Log the number of trackers found.
        # 记录找到的追踪器数量。
        logger.info(f'Successfully gathered {len(trackers)} trackers')

        # Save the trackers to a file.
        # 将追踪器保存到文件中。
        file = self.config.get('base', 'save_file')
        logger.info(f'Writing trackers to file: {file}')
        with open(file, 'w') as f:
            f.write('\n'.join(trackers))

    def create_downloader(self) -> Downloader:
        """
        Creates a Downloader instance based on the configuration.
        根据配置创建下载器实例。
        """
        thread_pool_size = self.config.get('base', 'thread_pool_size')
        default_headers = self.config.get('request', 'default_headers')
        timeout = self.config.get('request', 'timeout')

        # Log the creation of the downloader.
        # 记录下载器的创建信息。
        logger.info(f'Create downloader with args: thread_pool_size={thread_pool_size}, '
                    f'default_headers={default_headers}, timeout={timeout}')

        # Instantiate and return the Downloader.
        # 实例化并返回下载器。
        return Downloader(default_headers=default_headers, timeout=timeout, workers=thread_pool_size)

    def create_analysis(self) -> Analysis:
        """
        Creates an Analysis instance and loads trackers from the configuration.
        创建分析器实例，并从配置中加载追踪器。
        """
        analysis = Analysis()
        tracker = self.config.get('base', 'tracker')

        # Load each tracker into the Analysis instance.
        # 将每个追踪器加载到分析器实例中。
        for i in tracker:
            method = self.config.get(f'tracker_{i}', 'method')
            analysis.load(self.config.get(f'tracker_{i}', 'url'), method)
            logger.info(f'Load tracker {i} with method {method}')

        return analysis

    def gather_url(self) -> list[tuple[str, dict]]:
        """
        Yields URLs and their corresponding headers from the configuration.
        从配置中生成URL及其对应的头部信息。
        """
        logger.info('Gathering url...')
        tracker = self.config.get('base', 'tracker')

        for i in tracker:
            yield self.config.get(f'tracker_{i}', 'url'), self.config.get(f'tracker_{i}', 'headers')


class Loop(object):
    """
    A class to handle looping execution of the Main class at regular intervals.
    循环执行主类的类，以固定的时间间隔运行。
    """
    def __init__(self, target: Main, interval: int = None):
        self.target = target

        if interval:
            self.interval = interval
        else:
            self.interval = self.calculate_interval()

    @staticmethod
    def calculate_interval():
        """
        Calculates the interval for loop execution based on the configuration.
        根据配置计算循环执行的间隔。
        """
        config = Config()
        return (
                config.get('interval', 'second') +
                config.get('interval', 'minute') * 60 +
                config.get('interval', 'hour') * 60 * 60 +
                config.get('interval', 'day') * 60 * 60 * 24
        )

    def run(self):
        """
        Runs the loop, handling exceptions and keyboard interrupts.
        运行循环，处理异常和键盘中断。
        """
        try:
            self._main()
        except KeyboardInterrupt:
            logger.info(f'Program exit successfully')
            print('Program exit successfully')

    def _main(self):
        """
        The main loop that repeatedly runs the target's `run` method.
        主循环，重复运行目标的 `run` 方法。
        """
        while True:
            try:
                self.target.run()
            except Exception as e:
                logger.error(f'An error occurred while running main: {e}', exc_info=True)
            finally:
                sleep(self.interval)


if __name__ == '__main__':
    # Initialize the Main and Loop instances.
    # 初始化主类和循环类实例。
    main_instance = Main()
    loop_instance = Loop(main_instance)

    # Start the loop.
    # 开始循环。
    loop_instance.run()
