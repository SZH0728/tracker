# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 定义 tracker 项目的领域异常体系。
@details 所有项目级错误共享 TrackerError 基类，具体模块异常保持并列且集中管理。
"""


class TrackerError(Exception):
    """
    @brief 表示 tracker 项目的领域错误。
    @details 作为所有项目级自定义错误的统一基类，便于调用方按领域捕获异常。
    """


class ConfigError(TrackerError):
    """
    @brief 表示配置语法或通用字段无效。
    @details 调用方可在服务绑定前捕获此异常并终止启动。
    """


class ParserError(TrackerError):
    """
    @brief 表示响应内容、解析器选项或候选 URL 无效。
    @details 有效但不含 tracker URL 的响应由解析器返回空列表，而不是抛出此异常。
    """


if __name__ == '__main__':
    pass
