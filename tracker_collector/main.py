# -*- coding:utf-8 -*-
# AUTHOR: Sun

from logging import getLogger
from time import sleep

import log
from config import Config
from download import Downloader
from analysis import Analysis

logger = getLogger(__name__)
config = Config()


def create_downloader():
    thread_pool_size = config.get('base', 'thread_pool_size')
    default_headers = config.get('request', 'default_headers')
    timeout = config.get('request', 'timeout')
    logger.info(f'Create downloader with args: thread_pool_size={thread_pool_size}, '
                f'default_headers={default_headers}, timeout={timeout}')
    return Downloader(default_headers=default_headers, timeout=timeout, workers=thread_pool_size)


def create_analysis():
    analysis = Analysis()
    tracker = config.get('base', 'tracker').split(',')

    for i in tracker:
        i = i.strip()
        analysis.load(config.get(f'tracker_{i}', 'url'), config.get(f'tracker_{i}', 'method'))
        logger.info(f'Load tracker {i} with method {config.get(f"tracker_{i}", "method")}')

    return analysis


def gather_url():
    logger.info('Gathering url...')
    tracker = config.get('base', 'tracker').split(',')

    for i in tracker:
        i = i.strip()
        yield config.get(f'tracker_{i}', 'url'), config.get(f'tracker_{i}', 'headers')


def main():
    logger.info('Starting fetching data...')
    trackers: list[str] = []

    downloader = create_downloader()
    analysis = create_analysis()

    for url, headers in gather_url():
        downloader.get(url, headers=headers)

    for result, request in downloader.complete():
        if isinstance(result, Exception):
            continue

        trackers += analysis.analyze(request.full_url, result)

    trackers: set[str] = set(trackers)
    logger.info(f'Successfully gathered {len(trackers)} trackers')

    file = config.get('base', 'save_file')
    logger.info(f'Writing trackers to file: {file}')
    with open(file, 'w') as f:
        f.write('\n'.join(trackers))


def loop():
    while True:
        logger.info('')

        interval = (
                config.get('interval', 'second') +
                config.get('interval', 'minute') * 60 +
                config.get('interval', 'hour') * 60 * 60 +
                config.get('interval', 'day') * 60 * 60 * 24
        )

        try:
            main()
        except Exception as e:
            logger.error(f'An error occurred while running main: {e}', exc_info=True)
        finally:
            sleep(interval)


if __name__ == '__main__':
    try:
        loop()
    except KeyboardInterrupt:
        logger.info(f'Program exit successfully')
        print('Program exit successfully')
