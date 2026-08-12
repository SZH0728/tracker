# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证配置加载边界的 pytest 行为。
@details 使用临时 INI 文件覆盖不可变快照、重载和 source 级请求字段校验。
"""

from pathlib import Path

import pytest

from config import Config, ConfigError, RawConfig

VALID_CONFIGURATION = """[global]
port = 8080
output_file = /data/trackers.txt
refresh_interval = 3600

[tracker.public]
url = https://example.invalid/trackers.txt
header = {"Accept": "text/plain"}
request_timeout = 15
retry = 3
retry_interval = 2
parser = text-lines-v1

[parser.json]
base = json-array-v1
list_key = trackers
"""


def write_configuration(path: Path, content: str) -> None:
    """
    @brief 写入测试配置文件。
    @param path 临时配置文件路径
    @param content 要写入的 INI 内容
    @return 无返回值。
    """
    path.write_text(content, encoding='utf-8')


def test_config_loads_immutable_ordered_records(tmp_path: Path) -> None:
    """
    @brief 验证有效配置会生成有序的不可变记录。
    @param tmp_path pytest 提供的临时目录
    @return 无返回值。
    """
    path = tmp_path / 'tracker.ini'
    write_configuration(path, VALID_CONFIGURATION)

    loaded_config = Config(path).config

    assert isinstance(loaded_config, RawConfig)
    assert loaded_config.global_config.port == 8080
    assert loaded_config.tracker_sources[0].name == 'public'
    assert loaded_config.tracker_sources[0].headers == (('Accept', 'text/plain'),)
    assert loaded_config.tracker_sources[0].request_timeout == 15
    assert loaded_config.tracker_sources[0].retry == 3
    assert loaded_config.tracker_sources[0].retry_interval == 2
    assert loaded_config.parser_sections[0].options == (('list_key', 'trackers'),)
    with pytest.raises(AttributeError):
        loaded_config.global_config.port = 9000  # type: ignore[misc]  # 验证冻结记录不可修改


def test_config_reload_replaces_only_successful_snapshot(tmp_path: Path) -> None:
    """
    @brief 验证失败重载不会覆盖最后一次成功快照。
    @param tmp_path pytest 提供的临时目录
    @return 无返回值。
    """
    valid_path = tmp_path / 'valid.ini'
    invalid_path = tmp_path / 'invalid.ini'
    write_configuration(valid_path, VALID_CONFIGURATION)
    write_configuration(invalid_path, '[global]\nport = invalid\n')
    configuration = Config(valid_path)
    previous_snapshot = configuration.config

    with pytest.raises(ConfigError):
        configuration.reload(invalid_path)

    assert configuration.path == invalid_path
    assert configuration.config is previous_snapshot


@pytest.mark.parametrize('key', ('request_timeout', 'retry', 'retry_interval'))
def test_config_rejects_missing_tracker_request_fields(tmp_path: Path, key: str) -> None:
    """
    @brief 验证每个 tracker 都必须提供请求限制字段。
    @param tmp_path pytest 提供的临时目录
    @param key 被移除的 tracker 请求字段
    @return 无返回值。
    """
    path = tmp_path / 'invalid.ini'
    content = VALID_CONFIGURATION.replace(f'{key} = {15 if key == "request_timeout" else 3 if key == "retry" else 2}\n', '')
    write_configuration(path, content)

    with pytest.raises(ConfigError, match='缺少必需键'):
        Config(path)


@pytest.mark.parametrize('key', ('request_timeout', 'retry', 'retry_interval'))
def test_config_rejects_invalid_tracker_request_fields(tmp_path: Path, key: str) -> None:
    """
    @brief 验证 tracker 请求限制字段必须为非负整数。
    @param tmp_path pytest 提供的临时目录
    @param key 待替换的 tracker 请求字段
    @return 无返回值。
    """
    path = tmp_path / 'invalid.ini'
    content = VALID_CONFIGURATION.replace(f'{key} = {15 if key == "request_timeout" else 3 if key == "retry" else 2}', f'{key} = -1')
    write_configuration(path, content)

    with pytest.raises(ConfigError, match='必须为非负十进制整数'):
        Config(path)


@pytest.mark.parametrize(
    ('replacement', 'message'),
    [
        ('unexpected = value\n', '包含未知键'),
        ('request_timeout = 15\n', '包含未知键'),
        ('[unsupported]\nvalue = 1\n', '包含不支持的配置节'),
        ('header = []', 'header 必须为 JSON 对象'),
    ],
)
def test_config_rejects_invalid_structure(tmp_path: Path, replacement: str, message: str) -> None:
    """
    @brief 验证配置结构错误会抛出领域异常。
    @param tmp_path pytest 提供的临时目录
    @param replacement 要替换或附加的配置内容
    @param message 预期错误消息片段
    @return 无返回值。
    """
    path = tmp_path / 'invalid.ini'
    if replacement == 'unexpected = value\n':
        content = VALID_CONFIGURATION.replace('parser = text-lines-v1\n', f'parser = text-lines-v1\n{replacement}')
    elif replacement == 'request_timeout = 15\n':
        content = VALID_CONFIGURATION.replace('refresh_interval = 3600\n', f'refresh_interval = 3600\n{replacement}')
    elif replacement.startswith('header'):
        content = VALID_CONFIGURATION.replace('header = {"Accept": "text/plain"}', replacement)
    else:
        content = VALID_CONFIGURATION + replacement
    write_configuration(path, content)

    with pytest.raises(ConfigError, match=message):
        Config(path)


if __name__ == '__main__':
    pass
