# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 集中定义 tracker 数据边界的不可变记录。
@details 本模块仅声明配置加载与业务模块之间传递的结构化数据，不执行文件、网络或其他外部操作。
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RawGlobalConfig(object):
    """
    @brief 表示尚未装配的全局服务设置。
    @details 字段已完成通用标量校验，但尚未触发任何运行时行为。
    """

    port: int                # HTTP 服务监听端口
    output_file: str         # 规范 tracker 输出文件路径
    refresh_interval: int    # 刷新周期秒数


@dataclass(frozen=True, slots=True)
class RawTrackerSource(object):
    """
    @brief 表示一个按声明顺序处理的上游 tracker 来源。
    @details 保留不可变的请求配置与解析器引用，供请求器和解析器边界模块按各自职责消费。
    """

    name: str                             # tracker 配置节的别名
    url: str                              # 请求地址

    headers: tuple[tuple[str, str], ...]  # 已解码且保持声明顺序的请求头
    request_timeout: int                  # 单次请求连接与读取的超时秒数
    retry: int                            # 请求失败后允许额外执行的次数
    retry_interval: int                   # 两次请求尝试之间的等待秒数

    parser: str                           # 配置的解析器别名或基础名称


@dataclass(frozen=True, slots=True)
class RawParserSection(object):
    """
    @brief 表示一个已配置解析器的原始字符串选项。
    @details base 与其余选项保持未解释状态，解析器模块负责后续验证和包装。
    """

    name: str                             # parser 配置节的别名
    base: str                             # 基础解析器名称
    options: tuple[tuple[str, str], ...]  # 除 base 外的原始字符串选项


@dataclass(frozen=True, slots=True)
class RawConfig(object):
    """
    @brief 汇集经通用字段校验后的原始配置。
    @details 元组保留 tracker 与 parser 节的声明顺序，避免向下游暴露可变配置容器。
    """

    global_config: RawGlobalConfig                 # 全局服务设置
    tracker_sources: tuple[RawTrackerSource, ...]  # 有序上游来源
    parser_sections: tuple[RawParserSection, ...]  # 有序解析器配置节


if __name__ == '__main__':
    pass
